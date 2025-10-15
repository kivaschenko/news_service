import openai
from django.conf import settings
from celery import shared_task
from .models import Article
from .utils import fetch_article


@shared_task
def fetch_and_summarize_article(url: str):
    data = fetch_article(url)
    article, created = Article.objects.get_or_create(
        source_url=url,
        defaults={
            "title": data["title"],
            "content": data["content"],
        },
    )
    if not created:
        return  # Article already exists
    # Summarize the article using OpenAI API
    openai.api_key = settings.OPENAI_API_KEY
    prompt = f"Summarize the following article in Ukrainian in 3-4 sentences:\n\n{article.content}"

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7,
        )
        summary = response.choices[0].message["content"].strip()
        article.summary = summary
        article.language = "uk"
        article.save()
    except Exception as e:
        article.summary = "Error generating summary."
        print(f"OpenAI API error: {e}")
        article.save()
    return (
        f"Article '{article.title}' processed successfully from {article.source_url}."
    )
