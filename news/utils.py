import requests
from bs4 import BeautifulSoup


def fetch_article(url: str) -> dict:
    """Парсинг HTML статті (спрощений варіант)"""
    resp = requests.get(url, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    title = soup.find("title").get_text()
    paragraphs = " ".join([p.get_text() for p in soup.find_all("p")[:5]])
    return {"title": title, "content": paragraphs}
