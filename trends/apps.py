import logging

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class TrendsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trends"

    def ready(self) -> None:
        """Initialize the sentence transformer model when Django starts."""
        # Only load model in production Cloud Run environment
        if not getattr(settings, "TESTING", False) and not settings.DEBUG:
            try:
                from trends.model_cache import model_cache

                model_name = getattr(
                    settings, "TRENDING_MODEL_NAME", "paraphrase-albert-small-v2"
                )
                logger.info(f"Pre-loading trending model: {model_name}")
                model_cache.get_model(model_name)
                logger.info("Trending model pre-loaded successfully")
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed, model will be loaded on first use"
                )
            except Exception as e:
                logger.error(f"Failed to pre-load trending model: {e}")
