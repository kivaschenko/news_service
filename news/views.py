from rest_framework import viewsets, serializers, filters
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.http import JsonResponse
from .models import Article
from .tasks import parse_feeds


class ArticleSerializer(serializers.ModelSerializer):
    is_translated = serializers.ReadOnlyField()

    class Meta:
        model = Article
        fields = [
            "id",
            "source_url",
            "title",
            "content",
            "summary",
            "language",
            "status",
            "published_at",
            "created_at",
            "updated_at",
            "word_count",
            "tags",
            "is_translated",
        ]
        read_only_fields = (
            "summary",
            "language",
            "created_at",
            "updated_at",
            "word_count",
            "status",
        )


class ArticleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""

    is_translated = serializers.ReadOnlyField()

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "summary",
            "language",
            "status",
            "published_at",
            "created_at",
            "word_count",
            "is_translated",
        ]


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all().order_by("-published_at", "-created_at")
    serializer_class = ArticleSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "summary", "tags"]
    ordering_fields = ["created_at", "published_at", "word_count"]
    ordering = ["-published_at", "-created_at"]

    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()
        language = self.request.query_params.get("language")
        status = self.request.query_params.get("status")

        if language:
            queryset = queryset.filter(language=language)
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_serializer_class(self):
        """Use lightweight serializer for list view"""
        if self.action == "list":
            return ArticleListSerializer
        return ArticleSerializer

    @action(detail=False, methods=["get"])
    def ukrainian(self, request):
        """Get only Ukrainian (translated) articles"""
        articles = self.queryset.filter(language="uk", status="completed")
        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get statistics about articles"""
        total = self.queryset.count()
        ukrainian = self.queryset.filter(language="uk").count()
        completed = self.queryset.filter(status="completed").count()

        return Response(
            {
                "total_articles": total,
                "ukrainian_articles": ukrainian,
                "completed_articles": completed,
                "processing_rate": f"{(completed / total * 100):.1f}%"
                if total > 0
                else "0%",
            }
        )


@api_view(["POST"])
def trigger_parse_feeds(request):
    """Manually trigger parsing of RSS feeds"""
    try:
        task = parse_feeds.delay()
        return JsonResponse(
            {"message": "Feed parsing triggered successfully", "task_id": task.id}
        )
    except Exception as e:
        return JsonResponse(
            {"error": f"Failed to trigger parsing: {str(e)}"}, status=500
        )
