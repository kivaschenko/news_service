from django.core.management.base import BaseCommand
from news.tasks import discover_and_process_articles


class Command(BaseCommand):
    help = "Manually trigger news article discovery and processing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            type=str,
            help="Process a specific URL instead of discovering articles",
        )

    def handle(self, *args, **options):
        if options["url"]:
            # Process a specific URL
            from news.tasks import process_single_article

            self.stdout.write(f"Processing specific URL: {options['url']}")

            try:
                task = process_single_article.delay(options["url"])
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Article processing task queued successfully. Task ID: {task.id}"
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to queue processing task: {str(e)}")
                )
        else:
            # Discover and process articles from news sites
            self.stdout.write("Starting news article discovery and processing...")

            try:
                task = discover_and_process_articles.delay()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Article discovery task queued successfully. Task ID: {task.id}"
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to queue discovery task: {str(e)}")
                )
