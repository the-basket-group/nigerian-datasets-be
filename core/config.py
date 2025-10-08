import base64
import json
import os
from typing import TypedDict

from dotenv import load_dotenv

load_dotenv()


class GoogleServiceAccount(TypedDict):
    type: str | None
    project_id: str | None
    private_key_id: str | None
    private_key: str | None
    client_email: str | None
    client_id: str | None
    auth_uri: str | None
    token_uri: str | None
    auth_provider_x509_cert_url: str | None
    client_x509_cert_url: str | None
    universe_domain: str | None


class Config:
    GOOGLE_CLIENT_ID: str | None
    GOOGLE_CLIENT_SECRET: str | None
    GOOGLE_REDIRECT_URI: str | None
    GOOGLE_AUTH_SCOPE: list[str]
    FRONTEND_URL: str | None
    JWT_ACCESS_TOKEN_SECRET: str | None
    JWT_ENCRYPTION_METHOD: str | None
    GOOGLE_SERVICE_ACCOUNT_INFO = GoogleServiceAccount | None
    BUCKET_NAME: str | None
    MAILGUN_API_KEY: str | None
    MAILGUN_DOMAIN: str | None

    def __init__(self) -> None:
        self.GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        self.GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
        self.GOOGLE_REDIRECT_URI = os.getenv(
            "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/users/google/callback/"
        )
        self.GOOGLE_AUTH_SCOPE = os.getenv("GOOGLE_AUTH_SCOPE", "email,profile").split(
            ","
        )
        self.FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.JWT_ACCESS_TOKEN_SECRET = os.getenv(
            "JWT_ACCESS_TOKEN_SECRET", "jwt-secret-key"
        )
        self.JWT_ENCRYPTION_METHOD = os.getenv("JWT_ENCRYPTION_METHOD", "HS256")

        # Handles file path, base64, or plain JSON
        gcp_key = os.getenv("GCP_SERVICE_ACCOUNT_KEY", "").strip()

        if gcp_key and os.path.isfile(gcp_key):
            with open(gcp_key) as f:
                gcp_key = f.read()
        elif gcp_key and not gcp_key.startswith("{"):
            try:
                gcp_key = base64.b64decode(gcp_key).decode("utf-8")
            except Exception:
                gcp_key = "{}"
        elif not gcp_key:
            gcp_key = "{}"

        self.GOOGLE_SERVICE_ACCOUNT_INFO = json.loads(gcp_key)

        self.BUCKET_NAME = os.getenv("BUCKET_NAME")
        self.MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
        self.MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")


application_config = Config()
