from django.urls import path

from users.views import (
    GoogleAuthCallbackView,
    InitialGoogleSignInView,
    LoginUserView,
    RegisterUserView,
)

app_name = "users"

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register_user"),
    path("login/", LoginUserView.as_view(), name="login_user"),
    path(
        "initiate-google-signin/",
        InitialGoogleSignInView.as_view(),
        name="initiate_google_signin",
    ),
    path(
        "google/callback/",
        GoogleAuthCallbackView.as_view(),
        name="google_auth_callback",
    ),
]
