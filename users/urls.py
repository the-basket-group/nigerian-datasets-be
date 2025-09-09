from django.urls import path

<<<<<<< HEAD
from users.views import (
    GoogleAuthCallbackView,
    InitialGoogleSignInView,
    LoginUserView,
    RegisterUserView,
)
=======
from users.views import GoogleAuthCallbackView, InitialGoogleSignInView
>>>>>>> 1f6d02be3c74e19df5be3fe3f6b809d4d7898a50

app_name = "users"

urlpatterns = [
<<<<<<< HEAD
    path("register/", RegisterUserView.as_view(), name="register_user"),
    path("login/", LoginUserView.as_view(), name="login_user"),
=======
>>>>>>> 1f6d02be3c74e19df5be3fe3f6b809d4d7898a50
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
