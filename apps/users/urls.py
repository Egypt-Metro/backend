# apps/users/urls.py

from django.urls import path
from .views import RegisterView, LoginView, UserProfileView, UpdateUserView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # User registration endpoint (POST)
    path("register/", RegisterView.as_view(), name="register"),
    # User login endpoint (POST), provides access and refresh tokens
    path("login/", LoginView.as_view(), name="login"),
    # User profile view (GET) for authenticated users
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    # Update user profile (PATCH) for authenticated users
    path("profile/update/", UpdateUserView.as_view(), name="update-profile"),
    # Token refresh endpoint (POST), required to get a new access token
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]
