import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


def fetch_article(url: str) -> dict:
    """Парсинг HTML статті з покращеною обробкою помилок"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        resp = requests.get(url, timeout=15, headers=headers)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Try to extract title from various sources
        title = None
        for selector in [
            "title",
            "h1",
            ".entry-title",
            ".post-title",
            '[property="og:title"]',
        ]:
            element = soup.select_one(selector)
            if element:
                title = (
                    element.get_text(strip=True)
                    if hasattr(element, "get_text")
                    else element.get("content", "")
                )
                if title:
                    break

        if not title:
            title = f"Article from {urlparse(url).netloc}"

        # Extract content from paragraphs, prioritizing main content areas
        content_selectors = [
            ".entry-content p",
            ".post-content p",
            ".article-content p",
            ".content p",
            "main p",
            "article p",
            "p",
        ]

        paragraphs = []
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements and len(elements) >= 3:  # Prefer selectors with more content
                paragraphs = [
                    p.get_text(strip=True) for p in elements if p.get_text(strip=True)
                ]
                break

        # Fallback to all paragraphs if specific selectors don't work
        if not paragraphs:
            paragraphs = [
                p.get_text(strip=True)
                for p in soup.find_all("p")
                if p.get_text(strip=True)
            ]

        # Take first 10 paragraphs or until we have enough content
        content_parts = []
        word_count = 0
        for p in paragraphs[:10]:
            content_parts.append(p)
            word_count += len(p.split())
            if word_count > 500:  # Stop after ~500 words
                break

        content = (
            " ".join(content_parts) if content_parts else "Content extraction failed"
        )

        return {
            "title": title[:500],  # Limit title length
            "content": content,
        }

    except requests.RequestException as e:
        logger.error(f"Network error fetching {url}: {e}")
        return {
            "title": f"Error fetching article from {urlparse(url).netloc}",
            "content": f"Failed to fetch content: {str(e)}",
        }
    except Exception as e:
        logger.error(f"Parsing error for {url}: {e}")
        return {
            "title": f"Parsing error for {urlparse(url).netloc}",
            "content": f"Failed to parse content: {str(e)}",
        }
