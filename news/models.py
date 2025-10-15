from django.db import models


class Article(models.Model):
    source_url = models.URLField(unique=True)
    title = models.CharField(max_length=500)
    content = models.TextField()
    summary = models.TextField(blank=True, null=True)
    language = models.CharField(max_length=10, default="en")  # en / uk
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
