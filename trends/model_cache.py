import logging

from django.conf import settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class ModelCache:
    """Global singleton for caching sentence transformer models."""

    _instance = None
    _model: SentenceTransformer | None = None

    def __new__(cls) -> "ModelCache":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_model(self, model_name: str | None = None) -> SentenceTransformer:
        if model_name is None:
            model_name = getattr(settings, "TRENDING_MODEL_NAME", "all-MiniLM-L6-v2")

        if self._model is None:
            logger.info(f"Loading sentence transformer model: {model_name}")
            try:
                self._model = SentenceTransformer(model_name)
                logger.info(f"Model loaded successfully: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
                raise
        return self._model

    def clear_cache(self) -> None:
        """Clear cached model (useful for testing)."""
        self._model = None


# Global instance
model_cache = ModelCache()
