from typing import Any

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class JWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "users.auth.JWTAuthentication"
    name = "JWTAuthentication"

    def get_security_definition(self, auto_schema: Any) -> dict:
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer <token>"',
        }
