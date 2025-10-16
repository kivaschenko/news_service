from django.core.management.base import BaseCommand
from django.db.models import Count, Avg
from news.models import Article


class Command(BaseCommand):
    help = "Show statistics about processed articles"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== News Service Statistics ===\n"))

        # Total articles
        total_articles = Article.objects.count()
        self.stdout.write(f"Total articles: {total_articles}")

        # Articles by status
        status_stats = (
            Article.objects.values("status")
            .annotate(count=Count("status"))
            .order_by("status")
        )
        self.stdout.write("\nArticles by status:")
        for stat in status_stats:
            self.stdout.write(f"  {stat['status']}: {stat['count']}")

        # Articles by language
        language_stats = (
            Article.objects.values("language")
            .annotate(count=Count("language"))
            .order_by("-count")
        )
        self.stdout.write("\nArticles by language:")
        for stat in language_stats:
            self.stdout.write(f"  {stat['language']}: {stat['count']}")

        # Articles by domain
        domain_stats = (
            Article.objects.values("source_domain")
            .annotate(count=Count("source_domain"))
            .order_by("-count")[:10]
        )
        self.stdout.write("\nTop 10 source domains:")
        for stat in domain_stats:
            domain = stat["source_domain"] or "Unknown"
            self.stdout.write(f"  {domain}: {stat['count']}")

        # Word count statistics
        avg_word_count = Article.objects.aggregate(avg_words=Avg("word_count"))[
            "avg_words"
        ]
        if avg_word_count:
            self.stdout.write(f"\nAverage word count: {avg_word_count:.1f}")

        # Recent articles
        recent_articles = Article.objects.filter(status="completed").order_by(
            "-created_at"
        )[:5]
        if recent_articles:
            self.stdout.write("\nRecent completed articles:")
            for article in recent_articles:
                title = (
                    article.title[:60] + "..."
                    if len(article.title) > 60
                    else article.title
                )
                self.stdout.write(f"  - {title} ({article.language})")

        # Failed articles
        failed_count = Article.objects.filter(status="failed").count()
        if failed_count > 0:
            self.stdout.write(
                f"\n{self.style.WARNING(f'Warning: {failed_count} articles failed processing')}"
            )

            # Show recent failures
            recent_failures = Article.objects.filter(status="failed").order_by(
                "-created_at"
            )[:3]
            self.stdout.write("Recent failures:")
            for article in recent_failures:
                self.stdout.write(f"  - {article.source_url}")

        self.stdout.write(f"\n{self.style.SUCCESS('Statistics complete!')}")
