import logging
from collections import Counter
from collections.abc import Sequence
from typing import Any, cast

import numpy as np
import vertexai
from sklearn.metrics.pairwise import cosine_similarity
from vertexai.language_models import TextEmbeddingModel

logger = logging.getLogger(__name__)

try:
    import nltk
    from nltk.corpus import stopwords

    ENGLISH_STOPWORDS = set(stopwords.words("english"))
except LookupError:
    import nltk

    nltk.download("stopwords", quiet=True)
    from nltk.corpus import stopwords

    ENGLISH_STOPWORDS = set(stopwords.words("english"))

ENGLISH_STOPWORDS.update({"data", "statistics", "nigeria", "nigerian"})


class VertexAITrendingAnalyzer:
    """Vertex AI trending analyzer."""

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "text-multilingual-embedding-002",
    ):
        self.project_id = project_id
        self.model_name = model_name
        self.similarity_threshold = 0.7
        self.batch_size = 32

        vertexai.init(project=project_id, location=location)
        self.model = TextEmbeddingModel.from_pretrained(model_name)
        logger.info(f"Initialized Vertex AI with model: {model_name}")

    def encode_queries(self, queries: Sequence[str]) -> np.ndarray:
        """Get embeddings for queries."""
        if not queries:
            return np.array([])

        try:
            embeddings = []
            for i in range(0, len(queries), self.batch_size):
                batch = list(queries[i : i + self.batch_size])
                batch_embeddings = self.model.get_embeddings(cast(list, batch))
                embeddings.extend([emb.values for emb in batch_embeddings])
            return np.array(embeddings)
        except Exception as e:
            logger.error(f"Error encoding queries: {e}")
            return np.array([])

    def analyze_trending(
        self, queries: Sequence[str], top_n: int = 10
    ) -> dict[str, Any]:
        """Analyze trending patterns."""
        if not queries:
            return self._empty_response()

        query_counts = Counter(queries)

        try:
            embeddings = self.encode_queries(queries)
            if embeddings.size > 0:
                categories = self._semantic_clustering(queries, embeddings, top_n)
                method = "vertex_ai_embeddings"
            else:
                categories = self._frequency_clustering(query_counts, top_n)
                method = "frequency_fallback"
        except Exception:
            categories = self._frequency_clustering(query_counts, top_n)
            method = "frequency_fallback"

        return {
            "method": method,
            "trending_categories": categories,
            "analysis_stats": {
                "total_queries": len(queries),
                "unique_queries": len(query_counts),
                "clusters_created": len(categories),
                "model_name": self.model_name,
                "data_source": "user_searches",
            },
        }

    def find_similar_queries(
        self, queries: Sequence[str], target_query: str, top_k: int = 10
    ) -> list[dict[str, Any]]:
        """Find similar queries."""
        if not queries or not target_query:
            return []

        try:
            embeddings = self.encode_queries([target_query] + list(queries))
            if embeddings.size == 0:
                return []

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
        except Exception as e:
            logger.error(f"Similar queries failed: {e}")
            return []

    def _semantic_clustering(
        self, queries: Sequence[str], embeddings: np.ndarray, top_n: int
    ) -> list[dict]:
        """Orchestrates the semantic clustering process."""
        similarity_matrix = cosine_similarity(embeddings)
        clusters = self._create_clusters(similarity_matrix)

        categories = []
        for cluster_indices in clusters:
            if len(cluster_indices) < 2:
                continue

            category = self._build_category_from_cluster(
                cluster_indices, queries, embeddings
            )
            categories.append(category)

        return sorted(categories, key=lambda x: x["query_count"], reverse=True)[:top_n]

    def _create_clusters(self, similarity_matrix: np.ndarray) -> list[list[int]]:
        """Creates clusters of queries based on similarity."""
        clustered = set()
        clusters = []
        for i in range(len(similarity_matrix)):
            if i in clustered:
                continue

            similar_indices = [
                j
                for j, sim in enumerate(similarity_matrix[i])
                if sim >= self.similarity_threshold and j not in clustered
            ]

            clustered.update(similar_indices)
            clusters.append(similar_indices)
        return clusters

    def _build_category_from_cluster(
        self, cluster_indices: list[int], queries: Sequence[str], embeddings: np.ndarray
    ) -> dict:
        """Builds a category dictionary from a cluster of queries."""
        cluster_queries = [queries[i] for i in cluster_indices]
        cluster_embeddings = embeddings[cluster_indices]

        representative_query = self._get_representative_query(
            cluster_queries, cluster_embeddings
        )
        category_name = self._extract_category_name(representative_query)

        return {
            "category_name": category_name,
            "query_count": len(cluster_queries),
            "percentage_of_total": (len(cluster_queries) / len(queries)) * 100,
            "sample_queries": cluster_queries[:3],
            "representative_query": representative_query,
        }

    def _get_representative_query(
        self, cluster_queries: Sequence[str], cluster_embeddings: np.ndarray
    ) -> str:
        """Finds the most representative query in a cluster."""
        centroid = np.mean(cluster_embeddings, axis=0)
        distances = [np.linalg.norm(emb - centroid) for emb in cluster_embeddings]
        representative_idx = np.argmin(distances)
        return str(cluster_queries[int(representative_idx)])

    def _extract_category_name(self, representative_query: str) -> str:
        """Extract a meaningful category name from the representative query."""
        words = [
            word.title()
            for word in representative_query.lower().split()
            if len(word) > 2 and word not in ENGLISH_STOPWORDS and word.isalpha()
        ]

        return " ".join(words[:3]) if words else representative_query.title()

    def _frequency_clustering(self, query_counts: Counter, top_n: int) -> list[dict]:
        """Simple frequency-based clustering."""
        total_queries = sum(query_counts.values())

        return [
            {
                "category_name": query,
                "query_count": count,
                "percentage_of_total": (count / total_queries) * 100,
                "sample_queries": [query],
                "representative_query": query,
            }
            for query, count in query_counts.most_common(top_n)
        ]

    def _empty_response(self) -> dict[str, Any]:
        """Empty response structure."""
        return {
            "method": "no_data",
            "trending_categories": [],
            "analysis_stats": {
                "total_queries": 0,
                "unique_queries": 0,
                "clusters_created": 0,
                "model_name": self.model_name,
                "data_source": "user_searches",
            },
        }
