# authentication/urls.py
from django.urls import path
from .views import RequestPasswordResetView, ValidateTokenView, ResetPasswordView

urlpatterns = [
    path('password/reset/request/',
         RequestPasswordResetView.as_view(),
         name='password-reset-request'),
    path('password/reset/validate/',
         ValidateTokenView.as_view(),
         name='password-reset-validate'),
    path('password/reset/confirm/',
         ResetPasswordView.as_view(),
         name='password-reset-confirm'),
]
