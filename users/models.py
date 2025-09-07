from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    first_name = models.CharField(null=False)
    last_name = models.CharField(null=False)
    display_name = models.CharField(unique=True, null=False)
    email = models.EmailField(unique=True, null=False)
    role = models.CharField(choices=[("admin","admin"), ("moderator","moderator"), ("member","member")], default="member")
    status = models.CharField(choices=[("active", "active"), ("disabled", "disabled"), ("suspended", "suspended")], default="active")
    avatar_url = models.URLField(null=True, blank=True)

    REQUIRED_FIELDS = ["email"]