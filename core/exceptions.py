import logging
from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(
    exc: Exception, context: dict[str, Any]
) -> Response | None:
    response = exception_handler(exc, context)

    if isinstance(exc, ValueError):
        return Response(
            {
                "error": "invalid_parameters",
                "message": "Invalid query parameters",
                "details": {"parameter_error": str(exc)},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, ImportError):
        return Response(
            {
                "error": "dependency_error",
                "message": "A required dependency is not installed",
                "details": {"missing_dependency": str(exc)},
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if response is None:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return Response(
            {
                "error": "server_error",
                "message": "An unexpected error occurred on the server.",
                "details": {"error_details": str(exc)},
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
