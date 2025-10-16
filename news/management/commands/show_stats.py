from django.core.management.base import BaseCommand
from news.models import Article


class Command(BaseCommand):
    help = "Show statistics about articles in the database"

    def handle(self, *args, **options):
        total = Article.objects.count()
        by_language = {}
        by_status = {}

        for article in Article.objects.all():
            # Count by language
            lang = article.language
            by_language[lang] = by_language.get(lang, 0) + 1

            # Count by status
            status = article.status
            by_status[status] = by_status.get(status, 0) + 1

        self.stdout.write("\n=== News Service Statistics ===")
        self.stdout.write(f"Total articles: {total}")

        self.stdout.write("\nBy language:")
        for lang, count in by_language.items():
            percentage = (count / total * 100) if total > 0 else 0
            self.stdout.write(f"  {lang}: {count} ({percentage:.1f}%)")

        self.stdout.write("\nBy status:")
        for status, count in by_status.items():
            percentage = (count / total * 100) if total > 0 else 0
            self.stdout.write(f"  {status}: {count} ({percentage:.1f}%)")

        # Show recent articles
        recent = Article.objects.order_by("-created_at")[:5]
        if recent:
            self.stdout.write("\nRecent articles:")
            for article in recent:
                self.stdout.write(
                    f"  - {article.title[:60]}... ({article.language}, {article.status})"
                )

        self.stdout.write("")
