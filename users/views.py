import secrets
from datetime import UTC, datetime
from typing import TypedDict
from urllib.parse import urlencode
from uuid import uuid4

import requests
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.config import application_config
from core.utils import EmptySerializer, extract_base_url, send_email
from users.models import User
from users.permissions import is_accessible
from users.serializers import (
    LoginUserSerializer,
    RegisterUserSerializer,
    UserSerializer,
)


class GoogleUserInfoResponse(TypedDict):
    email: str
    name: str
    given_name: str
    family_name: str
    picture: str


class InitialGoogleSignInView(APIView):
    serializer_class = EmptySerializer

    def get(self, request: Request) -> Response:
        if (
            not application_config.GOOGLE_CLIENT_ID
            or not application_config.GOOGLE_CLIENT_SECRET
            or not application_config.GOOGLE_REDIRECT_URI
        ):
            raise APIException(detail={"message": "service unavailable"})
        scheme = f"{request.scheme}://"
        redirect_url = request.build_absolute_uri(reverse("users:google_auth_callback"))
        redirect_url = f"{redirect_url}".replace("http://", scheme)
        referrer = request.headers.get("Referer") or request.META.get("HTTP_REFERER")
        if referrer:
            referrer = extract_base_url(referrer)

        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        query_params = urlencode(
            {
                "client_id": application_config.GOOGLE_CLIENT_ID,
                "redirect_uri": redirect_url,
                "response_type": "code",
                "scope": " ".join(application_config.GOOGLE_AUTH_SCOPE),
                "state": referrer or str(uuid4()),
                "access_type": "offline",
                "prompt": "consent",
            }
        )

        return Response(
            data={"url": f"{base_url}?{query_params}"}, content_type="application/json"
        )


class GoogleAuthCallbackView(APIView):
    serializer_class = EmptySerializer

    def get(self, request: Request) -> HttpResponseRedirect:
        # state is being used to store the base url of the frontend
        state = request.GET.get("state")
        if state:
            state = extract_base_url(state)
        frontend_url = state or application_config.FRONTEND_URL

        try:
            if (
                not application_config.GOOGLE_CLIENT_ID
                or not application_config.GOOGLE_CLIENT_SECRET
                or not application_config.GOOGLE_REDIRECT_URI
            ):
                raise APIException(detail={"message": "service unavailable"})
            code = request.GET.get("code")

            scheme = f"{request.scheme}://"
            redirect_url = request.build_absolute_uri(
                reverse("users:google_auth_callback")
            )
            redirect_url = f"{redirect_url}".replace("http://", scheme)
            token_response = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": application_config.GOOGLE_CLIENT_ID,
                    "client_secret": application_config.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_url,
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
                    username=f"{user_profile['given_name']}-{secrets.token_urlsafe(8)}",
                    status="active",
                    avatar_url=user_profile["picture"],
                    role="member",
                )
                user_access_token = user.create_access_token()
                html_message = render_to_string(
                    "welcome_email.html",
                    {
                        "user_name": f"{user_profile['given_name']} {user_profile['family_name']}"
                    },
                )
                send_email(
                    emails=[user_profile["email"]],
                    subject="Welcome to Nigerian Datasets!",
                    content=html_message,
                )

            return redirect(f"{frontend_url}/auth/success?token={user_access_token}")
        except Exception:
            message = urlencode({"message": "An unexpected error occurred"})
            return redirect(f"{frontend_url}/auth/failure?{message}")


class RegisterUserView(CreateAPIView):
    serializer_class = RegisterUserSerializer

    def create(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        existing_users = User.objects.filter(
            Q(email=serializer.validated_data["email"].lower())
            | Q(username=serializer.validated_data["username"].lower())
        )

        if existing_users.count():
            raise ValidationError(
                detail={"message": "user with username or email already exists."}
            )

        first_name = serializer.validated_data["first_name"].title()
        last_name = serializer.validated_data["last_name"].title()
        email = serializer.validated_data["email"].lower()
        user = User.objects.create_user(
            username=serializer.validated_data["username"].lower(),
            email=email,
            password=serializer.validated_data["password"],
            first_name=first_name,
            last_name=last_name,
            status="active",
            avatar_url="",
            role="member",
        )

        html_message = render_to_string(
            "welcome_email.html", {"user_name": f"{first_name} {last_name}"}
        )
        send_email(
            emails=[email],
            subject="Welcome to Nigerian Datasets!",
            content=html_message,
        )

        user_response = UserSerializer(instance=user).data
        return Response(
            data={"message": "successfully registered user", "user": user_response}
        )


class LoginUserView(APIView):
    serializer_class = LoginUserSerializer

    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        existing_user = User.objects.filter(
            email=serializer.validated_data["email"]
        ).first()

        if not existing_user:
            raise ValidationError(detail={"message": "Invalid credentials"})

        if not existing_user.check_password(serializer.validated_data["password"]):
            raise ValidationError(detail={"message": "Invalid credentials"})

        access_token = existing_user.create_access_token()
        user_response = UserSerializer(instance=existing_user).data

        return Response(
            data={
                "message": "successfully logged in user",
                "user": user_response,
                "access_token": access_token,
            }
        )


class TestAuthView(APIView):
    permission_classes = [is_accessible("admin")]
    serializer_class = EmptySerializer

    def get(self, request: Request) -> Response:
        return Response(data={"success": True})


class GetCurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request: Request) -> Response:
        serializer = UserSerializer(instance=request.user)
        return Response(data={"success": True, "data": serializer.data})
