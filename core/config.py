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
        # self.GOOGLE_SERVICE_ACCOUNT_INFO = {
        #     "type": os.getenv("GOOGLE_SERVICE_TYPE"),
        #     "project_id": os.getenv("GOOGLE_SERVICE_PROJECT_ID"),
        #     "private_key_id": os.getenv("GOOGLE_SERVICE_PRIVATE_KEY_ID"),
        #     "private_key": os.getenv("GOOGLE_SERVICE_PRIVATE_KEY"),
        #     "client_email": os.getenv("GOOGLE_SERVICE_CLIENT_EMAIL"),
        #     "client_id": os.getenv("GOOGLE_SERVICE_CLIENT_ID"),
        #     "auth_uri": os.getenv("GOOGLE_SERVICE_AUTH_URI"),
        #     "token_uri": os.getenv("GOOGLE_SERVICE_TOKEN_URI"),
        #     "auth_provider_x509_cert_url": os.getenv("GOOGLE_SERVICE_AUTH_PROVIDER_x509_URL"),
        #     "client_x509_cert_url": os.getenv("GOOGLE_SERVICE_CLIENT_x509_CERT_URL"),
        #     "universe_domain": os.getenv("GOOGLE_SERVICE_UNIVERSE_DOMAIN")
        # }

        self.GOOGLE_SERVICE_ACCOUNT_INFO = json.loads(
            os.getenv("GCP_SERVICE_ACCOUNT_KEY", "{}")
        )
        self.BUCKET_NAME = os.getenv("BUCKET_NAME")


application_config = Config()
