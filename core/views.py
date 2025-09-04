from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    @extend_schema(
        summary="Health Check",
        description="Check if the API is running",
        responses={200: {"description": "API is healthy"}},
    )
    def get(self, request: Request) -> Response:
        return Response(
            {"status": "healthy", "message": "Nigerian Datasets API is running"}
        )
