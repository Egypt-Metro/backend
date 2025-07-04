# backend/metro/urls.py
"""
URL configuration for metro project.

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
# metro/urls.py

import logging

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.permissions import AllowAny

from metro import settings

from .views import check_dependencies, health_check, home

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# OpenAPI schema view
schema_view = get_schema_view(
    openapi.Info(
        title=f"{settings.PROJECT_NAME} API",
        default_version="v1",
        description="API documentation for Metro application",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="a.moh.nassar00@gmail.com"),
        license=openapi.License(name="MIT License", url="https://opensource.org/licenses/MIT"),
    ),
    public=True,
    permission_classes=(AllowAny,),
)

# Log schema_view after it is defined
# logger.debug(schema_view)

# Core URL patterns
urlpatterns = [
    # Admin
    path('admin/dashboard/', include('apps.dashboard.urls', namespace='dashboard')),    # Admin dashboard
    path('admin/dashboard', RedirectView.as_view(url='/admin/dashboard/'), name='dashboard_redirect'),
    path("admin/", admin.site.urls),  # Admin panel
    path('admin/login/', admin.site.login, name='admin_login'),  # Admin login
    path('admin/logout/', admin.site.logout, name='admin_logout'),  # Admin logout
    # path('admin/login/', auth_views.LoginView.as_view(
    #     template_name='admin/login.html',
    #     redirect_authenticated_user=True
    # ), name='admin_login'),  # Admin login
    # path('admin/logout/', auth_views.LogoutView.as_view(
    #     next_page='admin_login'
    # ), name='admin_logout'),    # Admin logout
    # Home
    path("", home, name="home"),  # Home view
    path("favicon.ico", RedirectView.as_view(url=settings.STATIC_URL + "favicon.ico")),  # Favicon
    # Check environment
    # path('check-environment/', check_environment, name='check_environment'),
    # Authentication
    path("accounts/", include("allauth.urls")),  # Allauth authentication
    # API Routes
    path("api/users/", include("apps.users.api.urls")),  # User
    path("api/stations/", include("apps.stations.urls")),  # Stations
    path("api/routes/", include("apps.routes.urls")),  # Routes
    path('api/trains/', include(('apps.trains.api.urls', 'trains'), namespace='train-api')),  # Trains
    path('api/tickets/', include('apps.tickets.api.urls', namespace='tickets')),  # Tickets
    path('api/wallet/', include('apps.wallet.api.urls')),  # Wallet
    path('api/analytics/', include('apps.analytics.urls')),  # Analytics
    # path("api/dashboard/", include("apps.dashboard.urls")),  # Admin Dashboard
    path("api/auth/", include("apps.authentication.urls")),  # Authentication
    # Miscellaneous
    path("health/", health_check, name="health_check"),  # Health check
    path('dependencies/', check_dependencies, name='check_dependencies'),  # Check dependencies
    # Documentation
    path("swagger.json", schema_view.without_ui(cache_timeout=0), name="schema-json"),  # Swagger JSON
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),  # Swagger UI
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),  # ReDoc
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Debug the URL loading process
# logger.debug('URL patterns: %s', [path.pattern for path in urlpatterns])

# Debug Toolbar (only for development)
# if settings.DEBUG:
#     import debug_toolbar  # type: ignore

#     urlpatterns += [
#         path('__debug__/', include(debug_toolbar.urls)),  # Debug toolbar
#         static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
#         path("silk/", include("silk.urls", namespace="silk"))
#     ]

# Static and media files (if DEBUG is enabled)
# if settings.DEBUG:
#     urlpatterns += static(
#         settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
#     )  # Media files
