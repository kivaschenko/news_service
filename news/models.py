from django.db import models


class Article(models.Model):
    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("uk", "Ukrainian"),
        ("ru", "Russian"),
        ("de", "German"),
        ("fr", "French"),
        ("es", "Spanish"),
        ("it", "Italian"),
        ("unknown", "Unknown"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    source_url = models.URLField(unique=True, help_text="URL of the original article")
    title = models.CharField(max_length=500, help_text="Article title")
    content = models.TextField(help_text="Full article content")
    summary = models.TextField(
        blank=True, null=True, help_text="AI-generated summary in Ukrainian"
    )
    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default="unknown",
        help_text="Language of the article",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Processing status",
    )
    published_at = models.DateTimeField(
        null=True, blank=True, help_text="Original publication date"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="When article was added to our system"
    )
    updated_at = models.DateTimeField(auto_now=True, help_text="Last update time")
    word_count = models.PositiveIntegerField(
        default=0, help_text="Number of words in content"
    )
    tags = models.CharField(
        max_length=500, blank=True, help_text="Comma-separated tags"
    )
    authors = models.CharField(max_length=300, blank=True, help_text="Article authors")
    meta_description = models.CharField(
        max_length=500, blank=True, help_text="Meta description from source"
    )
    top_image = models.URLField(blank=True, help_text="URL of the main article image")
    source_domain = models.CharField(
        max_length=100, blank=True, help_text="Domain of the source website"
    )

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["language"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["published_at"]),
        ]

    def __str__(self):
        return f"{self.title[:100]}..." if len(self.title) > 100 else self.title

    def save(self, *args, **kwargs):
        # Calculate word count
        if self.content:
            self.word_count = len(self.content.split())
        super().save(*args, **kwargs)

    @property
    def is_translated(self):
        """Check if article has been translated to Ukrainian"""
        return self.language == "uk" and self.summary
