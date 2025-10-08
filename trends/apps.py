import logging

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class TrendsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trends"

    def ready(self) -> None:
        """Initialize Vertex AI analyzer on Django startup to avoid first-request delays."""
        # Only initialize if GOOGLE_CLOUD_PROJECT is configured
        project_id = getattr(settings, "GOOGLE_CLOUD_PROJECT", None)
        if not project_id:
            logger.info(
                "Skipping Vertex AI initialization: GOOGLE_CLOUD_PROJECT not configured"
            )
            return

        try:
            from trends.analyzers import VertexAITrendingAnalyzer

            logger.info("Initializing Vertex AI analyzer...")
            analyzer = VertexAITrendingAnalyzer(
                project_id=project_id,
                location=getattr(settings, "VERTEX_AI_LOCATION", "us-central1"),
                model_name=getattr(
                    settings, "VERTEX_AI_MODEL", "text-multilingual-embedding-002"
                ),
            )

            # Store as a module-level singleton for reuse in views
            import trends.views

            trends.views.BaseVertexAIView._analyzer = analyzer
            logger.info("Vertex AI analyzer initialized successfully")
        except Exception as e:
            logger.warning(
                f"Failed to initialize Vertex AI analyzer at startup: {e}. "
                f"Will initialize on first request instead."
            )
