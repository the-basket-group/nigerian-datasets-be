import logging
from datetime import timedelta

from django.db import models
from django.utils import timezone

from users.models import User

logger = logging.getLogger(__name__)


class SearchQueryManager(models.Manager):
    def get_recent_queries(self, days: int) -> list[tuple[str, list[float] | None]]:
        """Extract, clean, and deduplicate recent search queries, returning (query, embedding) tuples."""
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            query_data = self.filter(created_at__gte=cutoff_date).values_list(
                "query", "embedding"
            )

            seen = set()
            unique_queries_with_embeddings = []
            for query, embedding in query_data:
                if isinstance(query, str):
                    cleaned = query.lower().strip()
                    if 3 < len(cleaned) <= 200 and cleaned not in seen:
                        seen.add(cleaned)
                        unique_queries_with_embeddings.append((cleaned, embedding))

            logger.info(
                f"Extracted {len(unique_queries_with_embeddings)} unique user search queries for analysis"
            )
            return unique_queries_with_embeddings
        except Exception as e:
            logger.error(f"Error extracting user search queries: {e}", exc_info=True)
            return []


class SearchQuery(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="search_queries"
    )
    query = models.TextField()
    embedding = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = SearchQueryManager()

    def __str__(self) -> str:
        return f"{self.user.email}: {self.query}"
