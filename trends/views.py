import logging
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from trends.analyzers import VectorTrendingAnalyzer
from trends.serializers import (
    ErrorResponseSerializer,
    HealthCheckResponseSerializer,
    SimilarQueriesRequestSerializer,
    SimilarQueriesResponseSerializer,
    TrendingAnalysisResponseSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema_view(
    get=extend_schema(
        summary="Get trending dataset categories",
        description="Analyzes dataset titles, descriptions, and tags using vector embeddings and clustering",
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
        tags=["Trending Analysis"],
    )
)
class TrendingAnalysisView(APIView):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._analyzer: VectorTrendingAnalyzer | None = None

    @property
    def analyzer(self) -> VectorTrendingAnalyzer:
        if self._analyzer is None:
            self._analyzer = VectorTrendingAnalyzer(
                model_name=getattr(settings, "TRENDING_MODEL_NAME", "all-MiniLM-L6-v2"),
                similarity_threshold=getattr(
                    settings, "TRENDING_SIMILARITY_THRESHOLD", 0.7
                ),
                batch_size=getattr(settings, "TRENDING_BATCH_SIZE", 32),
            )
        return self._analyzer  # type: ignore[return-value]

    def get(self, request: Request) -> Response:
        try:
            days = max(1, min(365, int(request.query_params.get("days", 30))))
            limit = max(1, min(50, int(request.query_params.get("limit", 10))))

            queries = self._extract_dataset_queries(days)
            if not queries:
                return Response(
                    {
                        "method": "no_data",
                        "trending_categories": [],
                        "similarity_analysis": {
                            "avg_global_similarity": 0.0,
                            "max_similarity": 0.0,
                        },
                        "analysis_stats": {
                            "total_queries": 0,
                            "unique_queries": 0,
                            "clusters_created": 0,
                            "embedding_dimensions": 0,
                            "clustering_method": "none",
                            "data_source": f"datasets_last_{days}_days",
                        },
                    }
                )

            result = self.analyzer.analyze_trending(
                queries, min_cluster_size=2, top_n=limit
            )
            result["analysis_stats"]["data_source"] = f"datasets_last_{days}_days"
            return Response(result)

        except ValueError as e:
            return Response(
                {
                    "error": "invalid_parameters",
                    "message": "Invalid query parameters",
                    "details": {"parameter_error": str(e)},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Trending analysis failed: {e}", exc_info=True)
            return Response(
                {
                    "error": "analysis_error",
                    "message": "Trending analysis failed",
                    "details": {"error_details": str(e)},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _extract_dataset_queries(self, days: int) -> list[str]:
        try:
            from datasets.models import Dataset

            cutoff_date = timezone.now() - timedelta(days=days)
            datasets = (
                Dataset.objects.filter(
                    created_at__gte=cutoff_date, is_public=True, status="published"
                )
                .select_related("owner")
                .prefetch_related("tags")
            )

            queries = []
            for dataset in datasets:
                if dataset.title:
                    queries.append(dataset.title.strip())
                if dataset.description:
                    desc = dataset.description.strip()
                    if len(desc) > 100:
                        first_sentence = desc.split(".")[0]
                        if len(first_sentence) > 20:
                            queries.append(first_sentence[:100].strip())
                    else:
                        queries.append(desc)
                for tag in dataset.tags.all():
                    if tag.name:
                        queries.append(tag.name.strip())
                if dataset.geography and dataset.geography != "Nigeria":
                    queries.append(f"{dataset.geography} data")
                if dataset.source_org:
                    queries.append(f"{dataset.source_org} dataset")

            seen = set()
            unique_queries = []
            for query in queries:
                if isinstance(query, str):
                    cleaned = query.lower().strip()
                    if 3 < len(cleaned) <= 200 and cleaned not in seen:
                        seen.add(cleaned)
                        unique_queries.append(cleaned)

            return unique_queries
        except Exception as e:
            logger.error(f"Error extracting dataset queries: {e}", exc_info=True)
            return []


@extend_schema_view(
    post=extend_schema(
        summary="Find similar queries to a target query",
        description="Finds semantically similar queries using vector embeddings and cosine similarity",
        request=SimilarQueriesRequestSerializer,
        responses={
            200: SimilarQueriesResponseSerializer,
            400: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["Trending Analysis"],
    )
)
class SimilarQueriesView(APIView):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._analyzer: VectorTrendingAnalyzer | None = None

    @property
    def analyzer(self) -> VectorTrendingAnalyzer:
        if self._analyzer is None:
            self._analyzer = VectorTrendingAnalyzer(
                model_name=getattr(settings, "TRENDING_MODEL_NAME", "all-MiniLM-L6-v2"),
                batch_size=getattr(settings, "TRENDING_BATCH_SIZE", 32),
            )
        return self._analyzer  # type: ignore[return-value]

    def post(self, request: Request) -> Response:
        serializer = SimilarQueriesRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "error": "validation_error",
                    "message": "Invalid request data",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            data = serializer.validated_data
            similar_queries = self.analyzer.find_similar_queries(
                data["queries"], data["target_query"], data.get("top_k", 10)
            )
            return Response(
                {
                    "target_query": data["target_query"],
                    "similar_queries": similar_queries,
                    "total_found": len(similar_queries),
                }
            )
        except ImportError as e:
            return Response(
                {
                    "error": "dependency_error",
                    "message": "Required dependencies not installed",
                    "details": {"missing_dependency": str(e)},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.error(f"Similar queries search failed: {e}", exc_info=True)
            return Response(
                {
                    "error": "analysis_error",
                    "message": "Similar queries search failed",
                    "details": {"error_details": str(e)},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema_view(
    get=extend_schema(
        summary="Health check for trending analysis service",
        description="Returns service health status, model info and dependency availability",
        responses={200: HealthCheckResponseSerializer, 500: ErrorResponseSerializer},
        tags=["Trending Analysis"],
    )
)
class TrendingHealthView(APIView):
    def get(self, request: Request) -> Response:
        try:
            dependencies = self._check_dependencies()
            model_name = getattr(settings, "TRENDING_MODEL_NAME", "all-MiniLM-L6-v2")
            embedding_dimensions = 0

            if dependencies["sentence_transformers"] and dependencies["sklearn"]:
                try:
                    analyzer = VectorTrendingAnalyzer(model_name=model_name)
                    test_embeddings = analyzer.encode_queries(["test query"])
                    if len(test_embeddings) > 0:
                        embedding_dimensions = test_embeddings.shape[1]
                    dependencies["model_loading"] = True
                except Exception:
                    dependencies["model_loading"] = False

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
        deps = {}
        for module in ["sentence_transformers", "sklearn", "numpy"]:
            try:
                __import__(module)
                deps[module] = True
            except ImportError:
                deps[module] = False
        return deps
