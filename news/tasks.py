import logging
from urllib.parse import urlparse
from celery import shared_task
from .models import Article
from .utils import fetch_article, extract_links_from_news_site
from .summarizer import summarize_article

logger = logging.getLogger(__name__)

# List of news websites to scrape (not RSS feeds)
NEWS_SITES = [
    "https://www.agriculture.com/news",  # Agriculture news
    "https://www.agweb.com/news",  # Ag Web news
    "https://www.farm-online.com.au/news",  # Farm Online
    "https://www.agdaily.com/news",  # Agriculture Daily
    "https://www.farminguk.com/news",  # Farming UK
    "https://www.producer.com/news",  # The Producer news
    "https://www.grainnet.com/news",  # Grain Network
    "https://agfax.com/category/news",  # AgFax news
]


@shared_task
def discover_and_process_articles():
    """
    Main task to discover new articles from news sites and process them
    """
    total_processed = 0
    total_discovered = 0

    for site_url in NEWS_SITES:
        try:
            logger.info(f"Discovering articles from {site_url}")

            # Extract article links from the news site
            article_links = extract_links_from_news_site(site_url, max_links=5)
            total_discovered += len(article_links)

            logger.info(
                f"Found {len(article_links)} potential articles from {site_url}"
            )

            # Process each discovered article
            for article_url in article_links:
                # Queue the article for processing
                process_single_article.delay(article_url)
                total_processed += 1

        except Exception as e:
            logger.error(f"Error discovering articles from {site_url}: {e}")
            continue

    logger.info(
        f"Discovery completed: {total_discovered} articles found, {total_processed} queued for processing"
    )
    return f"Discovered {total_discovered} articles, queued {total_processed} for processing"


@shared_task
def process_single_article(url: str):
    """
    Process a single article: extract content, detect language, and create summary
    """
    try:
        # Check if article already exists
        if Article.objects.filter(source_url=url).exists():
            logger.info(f"Article from {url} already exists, skipping")
            return f"Article from {url} already exists"

        logger.info(f"Processing article from {url}")

        # Extract article content
        article_data = fetch_article(url)

        if (
            not article_data.get("content")
            or len(article_data.get("content", "")) < 100
        ):
            logger.warning(f"Insufficient content extracted from {url}")
            return f"Insufficient content from {url}"

        # Extract domain for categorization
        domain = urlparse(url).netloc

        # Create initial article record
        article = Article.objects.create(
            source_url=url,
            title=article_data.get("title", f"Article from {domain}"),
            content=article_data["content"],
            authors=article_data.get("authors", ""),
            meta_description=article_data.get("meta_description", ""),
            top_image=article_data.get("top_image", ""),
            source_domain=domain,
            language=article_data.get("language", "unknown"),
            word_count=int(article_data.get("word_count", "0")),
            status="processing",
        )
        # Save to get an ID
        article.save()
        # Set published date if available
        if article_data.get("publish_date"):
            try:
                from dateutil import parser

                article.published_at = parser.parse(article_data["publish_date"])
                article.save()
            except Exception as e:
                logger.warning(f"Could not parse publish date for {url}: {e}")

        # Generate summary using open-source model
        try:
            logger.info(f"Generating summary for article {article}")
            summary = summarize_article(article.content, language=article.language)

            # Update article with summary
            article.summary = summary
            article.status = "completed"
            article.save()

            logger.info(f"Successfully processed article {article}")
            return f"Successfully processed: {article.id} - {article}"  # type: ignore

        except Exception as summary_error:
            logger.error(f"Error generating summary for {url}: {summary_error}")
            article.summary = "Summary generation failed"
            article.status = "failed"
            article.save()
            return (
                f"Content extracted but summary failed for {url}: {str(summary_error)}"
            )

    except Exception as e:
        logger.error(f"Error processing article from {url}: {e}")

        # Try to update article status if it was created
        try:
            article = Article.objects.get(source_url=url)
            article.status = "failed"
            article.save()
        except Article.DoesNotExist:
            pass

        return f"Error processing article from {url}: {str(e)}"


@shared_task
def reprocess_failed_articles():
    """
    Retry processing articles that failed previously
    """
    failed_articles = Article.objects.filter(status="failed")[
        :10
    ]  # Process 10 at a time

    processed_count = 0

    for article in failed_articles:
        try:
            logger.info(f"Reprocessing failed article: {article.source_url}")

            # Try to re-extract content
            article_data = fetch_article(article.source_url)

            if article_data.get("content") and len(article_data["content"]) > 100:
                # Update content
                article.content = article_data["content"]
                article.language = article_data.get("language", "unknown")
                article.word_count = int(article_data.get("word_count", "0"))
                article.status = "processing"
                article.save()

                # Try to generate summary again
                summary = summarize_article(article.content, language=article.language)
                article.summary = summary
                article.status = "completed"
                article.save()

                processed_count += 1
                logger.info(f"Successfully reprocessed article {article.id}")
            else:
                logger.warning(f"Still insufficient content for {article.source_url}")

        except Exception as e:
            logger.error(f"Error reprocessing article {article.id}: {e}")
            continue

    return f"Reprocessed {processed_count} failed articles"


@shared_task
def cleanup_old_articles():
    """
    Clean up old articles to prevent database bloat
    """
    from datetime import datetime, timedelta

    # Delete articles older than 30 days that have failed status
    cutoff_date = datetime.now() - timedelta(days=30)

    deleted_count = Article.objects.filter(
        created_at__lt=cutoff_date, status="failed"
    ).delete()[0]

    logger.info(f"Cleaned up {deleted_count} old failed articles")
    return f"Cleaned up {deleted_count} old articles"


@shared_task
def process_specific_url(url: str):
    """
    Process a specific URL manually (for testing or manual additions)
    """
    return process_single_article(url)


# Legacy compatibility - keep the old function name but redirect to new logic
@shared_task
def parse_feeds():
    """Legacy function for backward compatibility"""
    return discover_and_process_articles()


@shared_task
def fetch_and_summarize_article(url: str):
    """Legacy function for backward compatibility"""
    return process_single_article(url)
