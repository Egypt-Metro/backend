# apps/users/api/urls.py
from django.urls import path

from .views import auth, profile, base, auth_test
from rest_framework_simplejwt.views import TokenRefreshView

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('register/', auth.RegisterView.as_view(), name='register'),
    path('login/', auth.LoginView.as_view(), name='login'),

    # Profile endpoints
    path('profile/', profile.UserProfileView.as_view(), name='user-profile'),
    path('profile/update/', profile.UpdateUserView.as_view(), name='update-profile'),

    # Token refresh endpoint
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    path("superusers/", base.get_superusers, name="get_superusers"),

    path('test-auth/', auth_test.test_auth, name='test-auth'),
]
