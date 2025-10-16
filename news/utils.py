import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False
    logger.warning("newspaper3k not available, using fallback extraction")

try:
    from langdetect import detect, LangDetectError
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not available, language detection disabled")


def extract_links_from_news_site(base_url: str, max_links: int = 10) -> List[str]:
    """Extract article links from a news website's main page"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(base_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = set()
        
        # Common selectors for article links
        article_selectors = [
            'article a[href]',
            '.article-title a[href]',
            '.post-title a[href]',
            '.entry-title a[href]',
            'h2 a[href]',
            'h3 a[href]',
            '.news-item a[href]',
            '.article-link[href]',
            'a[href*="/article/"]',
            'a[href*="/news/"]',
            'a[href*="/post/"]',
        ]
        
        for selector in article_selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href and isinstance(href, str):
                    # Convert relative URLs to absolute
                    full_url = urljoin(base_url, href)
                    # Filter out non-article URLs
                    if is_likely_article_url(full_url):
                        links.add(full_url)
                        if len(links) >= max_links:
                            break
            if len(links) >= max_links:
                break
        
        return list(links)[:max_links]
        
    except Exception as e:
        logger.error(f"Error extracting links from {base_url}: {e}")
        return []


def is_likely_article_url(url: str) -> bool:
    """Check if URL is likely to be an article"""
    url_lower = url.lower()
    
    # Skip common non-article URLs
    skip_patterns = [
        '/category/', '/tag/', '/author/', '/search/', '/archive/',
        '/login', '/register', '/contact', '/about', '/privacy',
        '.jpg', '.png', '.gif', '.pdf', '.css', '.js',
        '/wp-admin/', '/wp-content/', '#', 'javascript:',
        '/page/', '/sitemap', '/feed', '/rss'
    ]
    
    for pattern in skip_patterns:
        if pattern in url_lower:
            return False
    
    # Must be a reasonable length and contain path
    parsed = urlparse(url)
    if len(parsed.path) < 5 or parsed.path == '/':
        return False
        
    return True


def extract_title(soup: BeautifulSoup, url: str) -> str:
    """Extract title from various sources"""
    title_selectors = [
        'h1.article-title',
        'h1.post-title',
        'h1.entry-title',
        '.article-header h1',
        'article h1',
        'h1',
        'title',
        '[property="og:title"]',
        '[name="twitter:title"]',
    ]
    
    for selector in title_selectors:
        element = soup.select_one(selector)
        if element:
            if hasattr(element, "get_text"):
                title = element.get_text(strip=True)
            else:
                title = element.get("content", "")
            
            if title and len(str(title)) > 10:  # Reasonable title length
                return str(title)
    
    return f"Article from {urlparse(url).netloc}"


def extract_content(soup: BeautifulSoup) -> str:
    """Extract main content with improved selectors"""
    content_selectors = [
        '.article-content',
        '.post-content',
        '.entry-content',
        '.article-body',
        '.story-body',
        'article .content',
        'main article',
        '[role="main"] article',
        '.main-content article',
        'article',
        'main',
        '.content',
    ]
    
    for selector in content_selectors:
        container = soup.select_one(selector)
        if container:
            # Extract paragraphs from the container
            paragraphs = container.find_all(['p', 'div'], recursive=True)
            content_parts = []
            
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 20:  # Skip short snippets
                    content_parts.append(text)
            
            if content_parts and len(content_parts) >= 3:
                return ' '.join(content_parts[:20])  # Limit to first 20 paragraphs
    
    # Fallback: get all paragraphs
    paragraphs = soup.find_all('p')
    content_parts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20]
    
    return ' '.join(content_parts[:15]) if content_parts else "Content extraction failed"


def extract_publish_date(soup: BeautifulSoup) -> str:
    """Extract publish date from various sources"""
    date_selectors = [
        '[property="article:published_time"]',
        '[name="pubdate"]',
        '[name="date"]',
        '.publish-date',
        '.article-date',
        '.post-date',
        'time[datetime]',
        '.date',
    ]
    
    for selector in date_selectors:
        element = soup.select_one(selector)
        if element:
            date_str = element.get('content') or element.get('datetime') or element.get_text(strip=True)
            if date_str:
                try:
                    # Try to parse and format the date
                    from dateutil import parser
                    parsed_date = parser.parse(str(date_str))
                    return parsed_date.isoformat()
                except Exception:
                    return str(date_str)
    
    return ""


def fetch_article_with_newspaper(url: str) -> Dict:
    """Enhanced article extraction using newspaper3k library"""
    if not NEWSPAPER_AVAILABLE:
        return fetch_article_with_bs4(url)
        
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        # Try to detect language
        language = 'unknown'
        if article.text and LANGDETECT_AVAILABLE:
            try:
                detected_lang = detect(article.text[:1000])
                language = detected_lang
            except LangDetectError:
                language = 'unknown'
        
        # Extract publish date
        publish_date = ""
        if article.publish_date:
            publish_date = article.publish_date.isoformat()
        
        # Calculate word count
        word_count = len(article.text.split()) if article.text else 0
        
        return {
            'title': article.title or f"Article from {urlparse(url).netloc}",
            'content': article.text or "Failed to extract content",
            'summary': article.summary or "",
            'authors': ', '.join(article.authors) if article.authors else "",
            'publish_date': publish_date,
            'language': language,
            'word_count': str(word_count),
            'top_image': article.top_image or "",
            'meta_description': article.meta_description or "",
        }
        
    except Exception as e:
        logger.error(f"Newspaper extraction failed for {url}: {e}")
        # Fallback to BeautifulSoup method
        return fetch_article_with_bs4(url)


def fetch_article_with_bs4(url: str) -> Dict:
    """Fallback article extraction using BeautifulSoup"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        resp = requests.get(url, timeout=15, headers=headers)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside", "advertisement"]):
            element.decompose()

        # Extract title with better fallbacks
        title = extract_title(soup, url)
        
        # Extract main content
        content = extract_content(soup)
        
        # Extract meta description
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        if meta_tag:
            meta_desc = meta_tag.get("content", "")

        # Try to extract publish date
        publish_date = extract_publish_date(soup)
        
        # Detect language
        language = 'unknown'
        if content and LANGDETECT_AVAILABLE:
            try:
                detected_lang = detect(content[:1000])
                language = detected_lang
            except LangDetectError:
                language = 'unknown'
        
        word_count = len(content.split()) if content else 0

        return {
            "title": title[:500] if title else f"Article from {urlparse(url).netloc}",
            "content": content,
            "summary": "",
            "authors": "",
            "publish_date": publish_date or "",
            "language": language,
            "word_count": str(word_count),
            "top_image": "",
            "meta_description": meta_desc[:500] if meta_desc else "",
        }

    except requests.RequestException as e:
        logger.error(f"Network error fetching {url}: {e}")
        return create_error_response(url, f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Parsing error for {url}: {e}")
        return create_error_response(url, f"Parsing error: {str(e)}")


def create_error_response(url: str, error_msg: str) -> Dict:
    """Create standardized error response"""
    return {
        "title": f"Error fetching article from {urlparse(url).netloc}",
        "content": f"Failed to fetch content: {error_msg}",
        "summary": "",
        "authors": "",
        "publish_date": "",
        "language": "unknown",
        "word_count": "0",
        "top_image": "",
        "meta_description": "",
    }


def fetch_article(url: str) -> Dict:
    """Main function to fetch article - tries newspaper3k first, falls back to BeautifulSoup"""
    try:
        # Try newspaper3k first (more robust)
        result = fetch_article_with_newspaper(url)
        
        # If newspaper3k didn't get good content, try BeautifulSoup
        if not result.get('content') or len(result.get('content', '')) < 100:
            logger.info(f"Newspaper3k extraction was poor for {url}, trying BeautifulSoup")
            bs4_result = fetch_article_with_bs4(url)
            if len(bs4_result.get('content', '')) > len(result.get('content', '')):
                result = bs4_result
        
        return result
        
    except Exception as e:
        logger.error(f"All extraction methods failed for {url}: {e}")
        return create_error_response(url, str(e))