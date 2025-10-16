from django.core.management.base import BaseCommand
from news.tasks import parse_feeds


class Command(BaseCommand):
    help = "Manually trigger RSS feed parsing"

    def handle(self, *args, **options):
        self.stdout.write("Starting RSS feed parsing...")

        try:
            task = parse_feeds.delay()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Feed parsing task queued successfully. Task ID: {task.id}"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to queue parsing task: {str(e)}")
            )
