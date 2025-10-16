from django.contrib import admin
from .models import Article
from .tasks import fetch_and_summarize_article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = [
        "title_short",
        "language",
        "status",
        "word_count",
        "is_translated",
        "created_at",
        "published_at",
    ]
    list_filter = ["language", "status", "created_at", "published_at"]
    search_fields = ["title", "summary", "tags", "source_url"]
    readonly_fields = ["created_at", "updated_at", "word_count", "is_translated"]
    list_per_page = 25
    date_hierarchy = "created_at"

    fieldsets = (
        ("Basic Information", {"fields": ("title", "source_url", "status")}),
        ("Content", {"fields": ("content", "summary", "tags"), "classes": ("wide",)}),
        (
            "Metadata",
            {
                "fields": (
                    "language",
                    "published_at",
                    "word_count",
                    "created_at",
                    "updated_at",
                    "is_translated",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["reprocess_articles", "mark_as_completed"]

    def title_short(self, obj):
        """Display shortened title"""
        return (obj.title[:50] + "...") if len(obj.title) > 50 else obj.title

    title_short.short_description = "Title"

    def reprocess_articles(self, request, queryset):
        """Reprocess selected articles"""
        count = 0
        for article in queryset:
            fetch_and_summarize_article.delay(article.source_url)
            count += 1
        self.message_user(request, f"{count} articles queued for reprocessing.")

    reprocess_articles.short_description = "Reprocess selected articles"

    def mark_as_completed(self, request, queryset):
        """Mark selected articles as completed"""
        count = queryset.update(status="completed")
        self.message_user(request, f"{count} articles marked as completed.")
