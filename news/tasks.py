import openai
import feedparser
from django.conf import settings
from celery import shared_task
from .models import Article
from .utils import fetch_article

RSS_FEEDS = [
    "https://www.fao.org/news/rss-feed/en/",  # англомовний агросайт
    "https://latifundist.com/novosti/feed/",  # український агросайт (RSS)
    "https://www.world-grain.com/rss/",  # світові зернові ринки
    "https://www.agriculture.com/rss/",  # сільське господарство
]


@shared_task
def parse_feeds():
    """Проходиться по списку RSS-джерел і додає нові статті в обробку"""
    processed_count = 0
    for feed_url in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries[:5]:  # беремо останні 5 статей
                url = entry.link
                # Кидаємо в пайплайн обробки (парсинг + summary)
                fetch_and_summarize_article.delay(url)
                processed_count += 1
        except Exception as e:
            print(f"Error parsing feed {feed_url}: {e}")
    return f"Queued {processed_count} articles from {len(RSS_FEEDS)} feeds"


@shared_task
def fetch_and_summarize_article(url: str):
    """Завантажує статтю, перекладає та створює стислий опис українською"""
    try:
        # Перевіряємо чи стаття вже існує
        if Article.objects.filter(source_url=url).exists():
            return f"Article from {url} already exists"

        # Парсимо статтю
        data = fetch_article(url)

        # Створюємо статтю
        article = Article.objects.create(
            source_url=url,
            title=data["title"],
            content=data["content"],
            status="processing",
        )

        # Перекладаємо та стискаємо за допомогою OpenAI API
        if settings.OPENAI_API_KEY:
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

            # Визначаємо мову оригіналу та перекладаємо якщо потрібно
            detect_prompt = f"Determine the language of this text and translate to Ukrainian if it's in English. If already in Ukrainian, just return the original text:\n\n{article.content[:1000]}"

            translation_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator specializing in agricultural news.",
                    },
                    {"role": "user", "content": detect_prompt},
                ],
                max_tokens=1000,
                temperature=0.3,
            )

            translated_content = translation_response.choices[0].message.content
            if translated_content:
                translated_content = translated_content.strip()
            else:
                translated_content = article.content

            # Створюємо стислий опис українською
            summary_prompt = f"Create a concise summary in Ukrainian (3-4 sentences) of this agricultural/grain trade article:\n\n{translated_content}"

            summary_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert agricultural journalist creating concise summaries.",
                    },
                    {"role": "user", "content": summary_prompt},
                ],
                max_tokens=200,
                temperature=0.5,
            )

            summary = summary_response.choices[0].message.content
            if summary:
                summary = summary.strip()
            else:
                summary = "Не вдалося створити стислий опис"

            # Оновлюємо статтю
            article.content = translated_content
            article.summary = summary
            article.language = "uk"
            article.status = "completed"
            article.save()

            return f"Article '{article.title}' processed and translated successfully from {url}"
        else:
            article.summary = "OpenAI API key not configured"
            article.status = "failed"
            article.save()
            return f"Article '{article.title}' saved but not processed (no API key)"

    except Exception as e:
        # Update article status to failed if it was created
        try:
            article = Article.objects.get(source_url=url)
            article.status = "failed"
            article.save()
        except Article.DoesNotExist:
            pass
        print(f"Error processing article from {url}: {e}")
        return f"Error processing article from {url}: {str(e)}"
