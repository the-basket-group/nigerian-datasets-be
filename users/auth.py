from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from users.models import User


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request: Request) -> tuple[User, str] | None:
        token = request.headers.get("Authorization")
        if token is None:
            return None
        if len(token.split(" ")) != 2:
            return None
        token_key = token.split(" ")[0]
        bearer_token = token.split(" ")[1]
        if token_key != "Bearer":
            raise AuthenticationFailed("Invalid Authentication token")

        user_payload = User.validate_access_token(token=bearer_token)
        if not user_payload:
            raise AuthenticationFailed("Invalid Authentication token")
        user_id = user_payload.get("id")
        if not user_id:
            raise AuthenticationFailed("Invalid Authentication token")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist as e:
            raise AuthenticationFailed("Invalid user token") from e
        else:
            return (user, token)
