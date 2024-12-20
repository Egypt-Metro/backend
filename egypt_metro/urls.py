"""
URL configuration for egypt_metro project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from .views import health_check, home
# from django.conf import settings
# from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny

# OpenAPI schema view
schema_view = get_schema_view(
    openapi.Info(
        title="Metro API",
        default_version="v1",
        description="API documentation for Metro application",
        terms_of_service="https://www.google.com/policies/terms/",
        # contact=openapi.Contact(email="support@egyptmetro.com"),
        # license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(AllowAny,),
)

# Core URL patterns
urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),  # Admin panel

    # Home
    path("", home, name="home"),    # Home view

    # Authentication
    path("accounts/", include("allauth.urls")),  # Allauth authentication

    # API Routes
    path("api/users/", include("apps.users.urls")),  # User authentication
    path("api/stations/", include("apps.stations.urls")),  # Stations and trips

    # Miscellaneous
    path("health/", health_check, name="health_check"),  # Health check

    # Documentation
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),  # Swagger UI

    # path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]

# Debug Toolbar (only for development)
# if settings.DEBUG:
#     urlpatterns += [
#         path("__debug__/", include("debug_toolbar.urls")),  # Debug toolbar
#     ]

# Static and media files (if DEBUG is enabled)
# if settings.DEBUG:
#     urlpatterns += static(
#         settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
#     )  # Media files
