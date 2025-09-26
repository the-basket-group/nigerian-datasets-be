import logging
from collections import Counter
from typing import Any

import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics.pairwise import cosine_similarity

from trends.model_cache import model_cache

logger = logging.getLogger(__name__)


class VectorTrendingAnalyzer:
    """Vector-based trending analysis with semantic clustering."""

    def __init__(
        self,
        model_name: str = "paraphrase-albert-small-v2",
        similarity_threshold: float = 0.7,
        batch_size: int = 32,
    ):
        self.model_name = model_name
        self.similarity_threshold = max(0.1, min(0.99, similarity_threshold))
        self.batch_size = batch_size

    @property
    def model(self) -> Any:
        try:
            return model_cache.get_model(self.model_name)
        except ImportError as e:
            raise ImportError(
                "sentence-transformers required: pip install sentence-transformers"
            ) from e

    def encode_queries(self, queries: list[str]) -> np.ndarray:
        if not queries:
            return np.array([])
        processed = [q.lower().strip() for q in queries]
        return self.model.encode(  # type: ignore[no-any-return]
            processed, batch_size=self.batch_size, normalize_embeddings=True
        )

    def analyze_trending(
        self, queries: list[str], min_cluster_size: int = 2, top_n: int = 10
    ) -> dict[str, Any]:
        if not queries:
            return {
                "method": "vector_embeddings",
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
                },
            }

        if len(set(queries)) <= 1:
            unique_query = queries[0]
            return {
                "method": "single_query",
                "trending_categories": [
                    {
                        "category_name": unique_query,
                        "query_count": len(queries),
                        "percentage_of_total": 100.0,
                        "avg_similarity": 1.0,
                        "top_keywords": unique_query.lower().split()[:5],
                        "sample_queries": [unique_query],
                        "representative_query": unique_query,
                    }
                ],
                "similarity_analysis": {
                    "avg_global_similarity": 1.0,
                    "max_similarity": 1.0,
                },
                "analysis_stats": {
                    "total_queries": len(queries),
                    "unique_queries": 1,
                    "clusters_created": 1,
                    "embedding_dimensions": 0,
                    "clustering_method": "single_query",
                },
            }

        try:
            embeddings = self.encode_queries(queries)
            clusters, cluster_method = self._cluster_embeddings(
                embeddings, min_cluster_size
            )
            categories = self._analyze_clusters(queries, clusters, embeddings, top_n)
            similarity = self._calculate_similarity_metrics(embeddings)

            return {
                "method": "vector_embeddings",
                "trending_categories": categories,
                "similarity_analysis": similarity,
                "analysis_stats": {
                    "total_queries": len(queries),
                    "unique_queries": len(set(queries)),
                    "clusters_created": len(set(clusters))
                    - (1 if -1 in clusters else 0),
                    "embedding_dimensions": (
                        embeddings.shape[1] if len(embeddings) > 0 else 0
                    ),
                    "clustering_method": cluster_method,
                },
            }
        except Exception:
            query_counts = Counter(queries)
            categories = [
                {
                    "category_name": q,
                    "query_count": c,
                    "percentage_of_total": (c / len(queries)) * 100,
                    "avg_similarity": 1.0,
                    "top_keywords": q.lower().split()[:5],
                    "sample_queries": [q],
                    "representative_query": q,
                }
                for q, c in query_counts.most_common(top_n)
            ]
            return {
                "method": "frequency_fallback",
                "trending_categories": categories,
                "similarity_analysis": {
                    "avg_global_similarity": 0.0,
                    "max_similarity": 1.0,
                },
                "analysis_stats": {
                    "total_queries": len(queries),
                    "unique_queries": len(query_counts),
                    "clusters_created": len(categories),
                    "embedding_dimensions": 0,
                    "clustering_method": "frequency_based",
                },
            }

    def find_similar_queries(
        self, queries: list[str], target_query: str, top_k: int = 10
    ) -> list[dict[str, Any]]:
        if not queries or not target_query:
            return []

        try:
            embeddings = self.encode_queries([target_query] + queries)
            similarities = cosine_similarity(embeddings[0:1], embeddings[1:])[0]
            similar_indices = np.argsort(similarities)[::-1][:top_k]
            return [
                {
                    "query": queries[idx],
                    "similarity_score": float(similarities[idx]),
                    "rank": i + 1,
                }
                for i, idx in enumerate(similar_indices)
                if similarities[idx] >= 0.1
            ]
        except Exception:
            return []

    def _cluster_embeddings(
        self, embeddings: np.ndarray, min_cluster_size: int
    ) -> tuple[list[int], str]:
        eps = 1 - self.similarity_threshold
        dbscan_labels = DBSCAN(
            eps=eps, min_samples=min_cluster_size, metric="cosine"
        ).fit_predict(embeddings)
        n_clusters = len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0)

        if 2 <= n_clusters <= len(embeddings) // 2:
            return dbscan_labels.tolist(), "DBSCAN"

        n_kmeans = min(max(2, len(embeddings) // 3), 10)
        kmeans_labels = KMeans(
            n_clusters=n_kmeans, random_state=42, n_init=10
        ).fit_predict(embeddings)
        return kmeans_labels.tolist(), "KMeans"

    def _analyze_clusters(
        self,
        queries: list[str],
        cluster_labels: list[int],
        embeddings: np.ndarray,
        top_n: int,
    ) -> list[dict[str, Any]]:
        cluster_data: dict[int, dict[str, list[Any]]] = {}
        for i, (query, label) in enumerate(zip(queries, cluster_labels, strict=False)):
            if label != -1:
                if label not in cluster_data:
                    cluster_data[label] = {"queries": [], "embeddings": []}
                cluster_data[label]["queries"].append(query)
                cluster_data[label]["embeddings"].append(embeddings[i])

        categories = []
        for data in cluster_data.values():
            if len(data["queries"]) < 2:
                continue

            cluster_embeddings = np.array(data["embeddings"])
            similarities = cosine_similarity(cluster_embeddings)
            avg_similarity = np.mean(
                similarities[np.triu_indices_from(similarities, k=1)]
            )

            centroid = np.mean(cluster_embeddings, axis=0)
            rep_idx = np.argmax(cosine_similarity([centroid], cluster_embeddings)[0])

            words = [
                w
                for q in data["queries"]
                for w in q.lower().split()
                if len(w) > 2
                and w
                not in {
                    "the",
                    "a",
                    "an",
                    "and",
                    "or",
                    "but",
                    "in",
                    "on",
                    "at",
                    "to",
                    "for",
                    "of",
                    "with",
                    "by",
                }
            ]
            keywords = [w for w, _ in Counter(words).most_common(5)]
            category_name = (
                " ".join(keywords[:3])
                if keywords
                else " ".join(data["queries"][0].split()[:3])
            )

            categories.append(
                {
                    "category_name": category_name,
                    "query_count": len(data["queries"]),
                    "percentage_of_total": (len(data["queries"]) / len(queries)) * 100,
                    "avg_similarity": float(avg_similarity),
                    "top_keywords": keywords,
                    "sample_queries": data["queries"][:3],
                    "representative_query": data["queries"][rep_idx],
                }
            )

        return sorted(categories, key=lambda x: x["query_count"], reverse=True)[:top_n]

    def _calculate_similarity_metrics(self, embeddings: np.ndarray) -> dict[str, float]:
        if len(embeddings) < 2:
            return {"avg_global_similarity": 0.0, "max_similarity": 0.0}
        similarity_matrix = cosine_similarity(embeddings)
        upper_triangle = similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)]
        return {
            "avg_global_similarity": float(np.mean(upper_triangle)),
            "max_similarity": float(np.max(upper_triangle)),
        }
