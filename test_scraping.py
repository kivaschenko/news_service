#!/usr/bin/env python3
"""
Simple test script to verify the improved news scraping system
"""

import os
import sys
import django

# Setup Django
sys.path.append("/home/kostiantyn/projects/news_service")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "news_service.settings")
django.setup()

from news.utils import fetch_article, extract_links_from_news_site
from news.summarizer import summarize_article


def test_article_extraction():
    """Test article extraction from a specific URL"""
    print("=== Testing Article Extraction ===")

    # Test URL - using a reliable news site
    test_url = "https://www.agriculture.com/news"

    try:
        # Test link extraction
        print(f"Extracting links from: {test_url}")
        links = extract_links_from_news_site(test_url, max_links=3)

        if links:
            print(f"Found {len(links)} article links:")
            for i, link in enumerate(links, 1):
                print(f"  {i}. {link}")

            # Test article extraction on first link
            if links:
                first_link = links[0]
                print(f"\nTesting article extraction on: {first_link}")

                article_data = fetch_article(first_link)

                print(f"Title: {article_data.get('title', 'No title')}")
                print(f"Language: {article_data.get('language', 'Unknown')}")
                print(f"Word count: {article_data.get('word_count', '0')}")
                print(f"Content preview: {article_data.get('content', '')[:200]}...")

                # Test summarization if content is available
                if article_data.get("content") and len(article_data["content"]) > 100:
                    print("\n=== Testing Summarization ===")
                    try:
                        summary = summarize_article(article_data["content"])
                        print(f"Summary: {summary}")
                    except Exception as e:
                        print(f"Summarization failed: {e}")
                        print(
                            "Note: This is expected if transformers/torch are not installed"
                        )
        else:
            print("No article links found")

    except Exception as e:
        print(f"Error during testing: {e}")


def test_direct_url():
    """Test with a direct article URL"""
    print("\n=== Testing Direct URL ===")

    # You can replace this with any specific article URL
    test_urls = [
        "https://www.agriculture.com/news/crops/corn",
        "https://www.agweb.com/news",
    ]

    for url in test_urls:
        try:
            print(f"\nTesting: {url}")
            article_data = fetch_article(url)

            print(f"Title: {article_data.get('title', 'No title')[:100]}")
            print(f"Content length: {len(article_data.get('content', ''))}")
            print(f"Language: {article_data.get('language', 'Unknown')}")

            if len(article_data.get("content", "")) < 100:
                print("Warning: Extracted content is very short")

        except Exception as e:
            print(f"Error testing {url}: {e}")


if __name__ == "__main__":
    print("Testing improved news scraping system...\n")

    test_article_extraction()
    test_direct_url()

    print("\n=== Testing Complete ===")
    print("\nTo use the system:")
    print("1. Run: python manage.py parse_feeds")
    print("2. Check results: python manage.py show_stats")
    print("3. Process specific URL: python manage.py parse_feeds --url <URL>")
