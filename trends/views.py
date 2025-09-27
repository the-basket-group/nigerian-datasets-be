import logging

from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from trends.analyzers import VertexAITrendingAnalyzer
from trends.models import SearchQuery
from trends.serializers import (
    ErrorResponseSerializer,
    HealthCheckResponseSerializer,
    SimilarQueriesRequestSerializer,
    SimilarQueriesResponseSerializer,
    TrendingAnalysisResponseSerializer,
)

logger = logging.getLogger(__name__)


class BaseVertexAIView(APIView):
    """Base view with shared Vertex AI analyzer initialization."""

    _analyzer: VertexAITrendingAnalyzer | None = None

    @property
    def analyzer(self) -> VertexAITrendingAnalyzer:
        if self._analyzer is None:
            try:
                project_id = getattr(settings, "GOOGLE_CLOUD_PROJECT", None)
                if not project_id:
                    raise ValueError("GOOGLE_CLOUD_PROJECT setting is required")

                self._analyzer = VertexAITrendingAnalyzer(
                    project_id=project_id,
                    location=getattr(settings, "VERTEX_AI_LOCATION", "us-central1"),
                    model_name=getattr(
                        settings, "VERTEX_AI_MODEL", "text-multilingual-embedding-002"
                    ),
                )
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI analyzer: {e}")
                raise
        return self._analyzer


@extend_schema_view(
    get=extend_schema(
        summary="Get trending user search queries",
        description="Analyzes user search queries using Google Cloud Vertex AI embeddings and clustering",
        parameters=[
            OpenApiParameter(
                "days", int, description="Days to look back (default: 30)", default=30
            ),
            OpenApiParameter(
                "limit",
                int,
                description="Max categories to return (default: 10)",
                default=10,
            ),
        ],
        responses={
            200: TrendingAnalysisResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["trends"],
    )
)
class TrendingAnalysisView(BaseVertexAIView):
    """Trending analysis using Google Cloud Vertex AI embeddings."""

    def get(self, request: Request) -> Response:
        days = max(1, min(365, int(request.query_params.get("days", 30))))
        limit = max(1, min(50, int(request.query_params.get("limit", 10))))

        queries = SearchQuery.objects.get_recent_queries(days)
        if not queries:
            return Response(self.analyzer._empty_response())

        result = self.analyzer.analyze_trending(queries, top_n=limit)
        result["analysis_stats"]["data_source"] = f"user_searches_last_{days}_days"
        return Response(result)


@extend_schema_view(
    post=extend_schema(
        summary="Find related search queries",
        description="Finds semantically related search queries using Vertex AI embeddings and cosine similarity",
        request=SimilarQueriesRequestSerializer,
        responses={
            200: SimilarQueriesResponseSerializer,
            400: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["trends"],
    )
)
class RelatedSearchesView(BaseVertexAIView):
    """Find related search queries using Vertex AI embeddings."""

    def post(self, request: Request) -> Response:
        serializer = SimilarQueriesRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Get all unique queries from database
        database_queries = SearchQuery.objects.get_recent_queries(30)  # Last 30 days

        similar_queries = self.analyzer.find_similar_queries(
            database_queries, data["target_query"], data.get("top_k", 10)
        )
        return Response(
            {
                "target_query": data["target_query"],
                "similar_queries": similar_queries,
                "total_found": len(similar_queries),
            }
        )


@extend_schema_view(
    get=extend_schema(
        summary="Health check for trending analysis service",
        description="Returns service health status, Vertex AI model info and dependency availability",
        responses={200: HealthCheckResponseSerializer, 500: ErrorResponseSerializer},
        tags=["trends"],
    )
)
class TrendingHealthView(BaseVertexAIView):
    """Health check for Vertex AI trending analysis service."""

    def get(self, request: Request) -> Response:
        try:
            dependencies = self._check_dependencies()
            model_name = getattr(
                settings, "VERTEX_AI_MODEL", "text-multilingual-embedding-002"
            )
            embedding_dimensions = 0

            if dependencies["vertexai"] and dependencies["google_cloud_aiplatform"]:
                try:
                    project_id = getattr(settings, "GOOGLE_CLOUD_PROJECT", None)
                    if project_id:
                        analyzer = VertexAITrendingAnalyzer(
                            project_id=project_id, model_name=model_name
                        )
                        # Test with a simple query
                        test_embeddings = analyzer.encode_queries(["test query"])
                        if len(test_embeddings) > 0:
                            embedding_dimensions = test_embeddings.shape[1]
                        dependencies["vertex_ai_connection"] = True
                    else:
                        dependencies["vertex_ai_connection"] = False
                except Exception:
                    dependencies["vertex_ai_connection"] = False

            return Response(
                {
                    "status": "healthy" if all(dependencies.values()) else "degraded",
                    "model_name": model_name,
                    "embedding_dimensions": embedding_dimensions,
                    "dependencies_available": dependencies,
                    "timestamp": timezone.now(),
                }
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            return Response(
                {
                    "error": "health_check_error",
                    "message": "Health check failed",
                    "details": {"error_details": str(e)},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _check_dependencies(self) -> dict[str, bool]:
        """Check Vertex AI dependencies."""
        deps = {}
        dependencies = ["vertexai", "google.cloud.aiplatform", "sklearn", "numpy"]

        for module in dependencies:
            try:
                __import__(module)
                # Convert module names to valid dict keys
                key = module.replace(".", "_").replace("-", "_")
                deps[key] = True
            except ImportError:
                key = module.replace(".", "_").replace("-", "_")
                deps[key] = False
        return deps
