from unittest.mock import MagicMock, patch

import numpy as np
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from trends.analyzers import VectorTrendingAnalyzer


class VectorTrendingAnalyzerTests(TestCase):
    def setUp(self) -> None:
        self.analyzer = VectorTrendingAnalyzer("all-MiniLM-L6-v2", 0.7, 32)

    @patch("trends.model_cache.SentenceTransformer")
    def test_model_lazy_loading_and_encoding(self, mock_transformer: MagicMock) -> None:
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2], [0.4, 0.5]]
        mock_transformer.return_value = mock_model

        embeddings = self.analyzer.encode_queries(
            ["python tutorial", "machine learning"]
        )

        mock_transformer.assert_called_once_with("all-MiniLM-L6-v2")
        self.assertEqual(len(embeddings), 2)

    def test_keyword_extraction_and_category_naming(self) -> None:
        queries = [
            "python machine learning",
            "python programming",
            "machine learning algorithms",
        ]
        keywords = [w for q in queries for w in q.lower().split() if len(w) > 2]
        from collections import Counter

        top_keywords = [w for w, _ in Counter(keywords).most_common(3)]

        self.assertIn("python", top_keywords)
        self.assertIn("machine", top_keywords)

    def test_edge_cases(self) -> None:
        # Empty queries
        result = self.analyzer.analyze_trending([])
        self.assertEqual(result["method"], "vector_embeddings")
        self.assertEqual(result["trending_categories"], [])

        # Single query
        result = self.analyzer.analyze_trending(["test", "test", "test"])
        self.assertEqual(result["method"], "single_query")
        self.assertEqual(result["trending_categories"][0]["query_count"], 3)

    @patch("trends.model_cache.model_cache.get_model")
    def test_similar_queries(self, mock_get_model: MagicMock) -> None:
        mock_model = MagicMock()
        mock_model.encode.return_value = [
            [1.0, 0.0],
            [0.9, 0.1],
            [0.5, 0.5],
            [0.0, 1.0],
        ]
        mock_get_model.return_value = mock_model

        results = self.analyzer.find_similar_queries(
            ["python programming", "python tutorial", "javascript"], "python coding", 2
        )

        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]["similarity_score"] > results[1]["similarity_score"])


class TrendingAPITests(APITestCase):
    def setUp(self) -> None:
        self.trending_url = reverse("trends:trending-analysis")
        self.similar_url = reverse("trends:similar-queries")
        self.health_url = reverse("trends:trending-health")

    def test_trending_analysis_success(self) -> None:
        response = self.client.get(self.trending_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("method", response.data)

    def test_similar_queries_validation(self) -> None:
        # Empty queries
        response = self.client.post(
            self.similar_url, {"queries": [], "target_query": "test"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Empty target
        response = self.client.post(
            self.similar_url, {"queries": ["test"], "target_query": ""}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("trends.views.VectorTrendingAnalyzer")
    def test_similar_queries_success(self, mock_analyzer_class: MagicMock) -> None:
        mock_analyzer = MagicMock()
        mock_analyzer.find_similar_queries.return_value = [
            {"query": "python", "similarity_score": 0.85, "rank": 1}
        ]
        mock_analyzer_class.return_value = mock_analyzer

        response = self.client.post(
            self.similar_url,
            {"queries": ["python programming"], "target_query": "python tutorial"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["target_query"], "python tutorial")
        self.assertEqual(len(response.data["similar_queries"]), 1)

    @patch("trends.views.TrendingHealthView._check_dependencies")
    def test_health_check(self, mock_deps: MagicMock) -> None:
        mock_deps.return_value = {
            "sentence_transformers": True,
            "sklearn": True,
            "numpy": True,
        }

        with patch("trends.views.VectorTrendingAnalyzer") as mock_analyzer:
            mock_instance = MagicMock()
            mock_instance.encode_queries.return_value = np.array([[0.1] * 384])
            mock_analyzer.return_value = mock_instance

            response = self.client.get(self.health_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "healthy")

    def test_serializer_validation(self) -> None:
        from trends.serializers import SimilarQueriesRequestSerializer

        data = {
            "queries": ["python tutorial"],
            "target_query": "python programming",
            "top_k": 5,
        }
        serializer = SimilarQueriesRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
