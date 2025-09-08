import secrets
from datetime import UTC, datetime
from typing import TypedDict
from urllib.parse import urlencode
from uuid import uuid4

from django.http import HttpResponseRedirect
import requests
from django.shortcuts import redirect
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.config import application_config
from users.models import User


class GoogleUserInfoResponse(TypedDict):
    email: str
    name: str
    given_name: str
    family_name: str
    picture: str


class InitialGoogleSignInView(APIView):
    def get(self, request: Request) -> Response:
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        query_params = urlencode(
            {
                "client_id": application_config.GOOGLE_CLIENT_ID,
                "redirect_uri": application_config.GOOGLE_REDIRECT_URI,
                "response_type": "code",
                "scope": " ".join(application_config.GOOGLE_AUTH_SCOPE),
                "state": str(uuid4()),
                "access_type": "offline",
                "prompt": "consent",
            }
        )

        return Response(
            data={"url": f"{base_url}?{query_params}"}, content_type="application/json"
        )


class GoogleAuthCallbackView(APIView):
    def get(self, request: Request) -> HttpResponseRedirect:
        try:
            code = request.GET.get("code")
            token_response = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": application_config.GOOGLE_CLIENT_ID,
                    "client_secret": application_config.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": application_config.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )

            token_response.raise_for_status()
            access_token = token_response.json()["access_token"]

            user_info_response = requests.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            user_info_response.raise_for_status()
            user_profile: GoogleUserInfoResponse = user_info_response.json()

            user_access_token = None
            try:
                user = User.objects.get(email=user_profile["email"])
                user.last_login = datetime.now(tz=UTC)
                user.save()
                user_access_token = user.create_access_token()

            except User.DoesNotExist:
                user = User.objects.create(
                    email=user_profile["email"],
                    first_name=user_profile["given_name"],
                    last_name=user_profile["family_name"],
                    display_name=f"{user_profile['given_name']}-{secrets.token_urlsafe(8)}",
                    status="active",
                    avatar_url=user_profile["picture"],
                    role="member",
                )
                user_access_token = user.create_access_token()

            return redirect(
                f"{application_config.FRONTEND_URL}/auth/success?token={user_access_token}"
            )
        except Exception:
            message = urlencode({"message": "An unexpected error occurred"})
            return redirect(f"{application_config.FRONTEND_URL}/auth/failure?{message}")
