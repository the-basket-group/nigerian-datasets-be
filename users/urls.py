from django.urls import path
from users.views import InitialGoogleSignInView, GoogleAuthCallbackView

app_name = 'users'

urlpatterns = [
    path('initiate-google-signin/', InitialGoogleSignInView.as_view(), name='initiate_google_signin'),
    path('google/callback/', GoogleAuthCallbackView.as_view(), name='google_auth_callback')
]