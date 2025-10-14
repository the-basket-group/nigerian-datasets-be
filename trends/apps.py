import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class TrendsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trends"

    def ready(self) -> None:
        """App initialization hook. Vertex AI analyzer now uses lazy loading."""
        logger.info(
            "Trends app ready. Vertex AI will initialize on first request (lazy loading)."
        )
