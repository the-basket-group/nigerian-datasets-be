from typing import Any

from rest_framework import serializers


class SimilarQueriesRequestSerializer(serializers.Serializer):
    """Serializer for similar queries request data."""

    queries = serializers.ListField(
        child=serializers.CharField(max_length=500, min_length=1),
        min_length=1,
        max_length=1000,
        help_text="List of candidate queries to search within",
    )

    target_query = serializers.CharField(
        max_length=500,
        min_length=1,
        help_text="Target query to find similar ones for",
    )

    top_k = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=100,
        help_text="Number of similar queries to return (1-100)",
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Cross-field validation."""
        queries = attrs.get("queries", [])
        target_query = attrs.get("target_query", "")

        # Clean queries
        cleaned_queries = [q.strip() for q in queries if q.strip()]
        cleaned_target = target_query.strip()

        if not cleaned_queries:
            raise serializers.ValidationError(
                {"queries": "At least one valid query is required."}
            )

        if not cleaned_target:
            raise serializers.ValidationError(
                {"target_query": "Target query cannot be empty."}
            )

        attrs["queries"] = cleaned_queries
        attrs["target_query"] = cleaned_target

        return attrs


class TrendingCategorySerializer(serializers.Serializer):
    """Serializer for trending category data."""

    category_name = serializers.CharField()
    query_count = serializers.IntegerField()
    percentage_of_total = serializers.FloatField()
    avg_similarity = serializers.FloatField()
    top_keywords = serializers.ListField(child=serializers.CharField())
    sample_queries = serializers.ListField(child=serializers.CharField())
    representative_query = serializers.CharField()


class SimilarityAnalysisSerializer(serializers.Serializer):
    """Serializer for similarity analysis data."""

    avg_global_similarity = serializers.FloatField()
    max_similarity = serializers.FloatField()


class AnalysisStatsSerializer(serializers.Serializer):
    """Serializer for analysis statistics."""

    total_queries = serializers.IntegerField()
    unique_queries = serializers.IntegerField()
    clusters_created = serializers.IntegerField()
    embedding_dimensions = serializers.IntegerField()
    clustering_method = serializers.CharField()


class TrendingAnalysisResponseSerializer(serializers.Serializer):
    """Serializer for trending analysis response data."""

    method = serializers.CharField()
    trending_categories = TrendingCategorySerializer(many=True)
    similarity_analysis = SimilarityAnalysisSerializer()
    analysis_stats = AnalysisStatsSerializer()


class SimilarQuerySerializer(serializers.Serializer):
    """Serializer for similar query data."""

    query = serializers.CharField()
    similarity_score = serializers.FloatField()
    rank = serializers.IntegerField()


class SimilarQueriesResponseSerializer(serializers.Serializer):
    """Serializer for similar queries response data."""

    target_query = serializers.CharField()
    similar_queries = SimilarQuerySerializer(many=True)
    total_found = serializers.IntegerField()


class HealthCheckResponseSerializer(serializers.Serializer):
    """Serializer for health check response."""

    status = serializers.CharField()
    model_name = serializers.CharField()
    embedding_dimensions = serializers.IntegerField()
    dependencies_available = serializers.DictField()
    timestamp = serializers.DateTimeField()


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses."""

    error = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(required=False)
