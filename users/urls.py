from django.urls import path

from users.views import (
    GetCurrentUserView,
    GoogleAuthCallbackView,
    InitialGoogleSignInView,
    LoginUserView,
    RegisterUserView,
    TestAuthView,
)

app_name = "users"

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register_user"),
    path("login/", LoginUserView.as_view(), name="login_user"),
    path("test/", TestAuthView.as_view(), name="test_auth"),
    path("profile/", GetCurrentUserView.as_view(), name="user_profile"),
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
