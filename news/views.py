from rest_framework import viewsets, serializers
from .models import Article


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = "__all__"

    read_only_fields = ("summary", "language", "created_at")


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all().order_by("-published_at", "-created_at")
    serializer_class = ArticleSerializer
