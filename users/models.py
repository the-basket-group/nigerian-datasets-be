import uuid

import jwt
from django.contrib.auth.models import AbstractUser
from django.db import models

from core.config import application_config


class User(AbstractUser):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, unique=True, editable=False
    )
    first_name = models.CharField(null=False)
    last_name = models.CharField(null=False)
    display_name = models.CharField(unique=True, null=False)
    email = models.EmailField(unique=True, null=False)
    role = models.CharField(
        choices=[("admin", "admin"), ("moderator", "moderator"), ("member", "member")],
        default="member",
    )
    status = models.CharField(
        choices=[
            ("active", "active"),
            ("disabled", "disabled"),
            ("suspended", "suspended"),
        ],
        default="active",
    )
    avatar_url = models.URLField(blank=True)

    REQUIRED_FIELDS = ["email"]

    def create_access_token(self) -> str:
        user_data = {"id": str(self.id), "email": self.email, "role": self.role}
        return jwt.encode(
            user_data, application_config.JWT_ACCESS_TOKEN_SECRET, "HS256"
        )
