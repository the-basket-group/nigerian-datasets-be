import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    GOOGLE_CLIENT_ID: str | None
    GOOGLE_CLIENT_SECRET: str | None
    GOOGLE_REDIRECT_URI: str | None
    GOOGLE_AUTH_SCOPE: list[str]
    FRONTEND_URL: str | None
    JWT_ACCESS_TOKEN_SECRET: str | None

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


application_config = Config()
