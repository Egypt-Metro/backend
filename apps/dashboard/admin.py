from django.contrib import admin
from django.urls import path
from .views.dashboard_views import DashboardView


# Option 1: Patch the existing admin site (RECOMMENDED)
def get_admin_urls(urls):
    """Add dashboard URLs to the admin."""
    return urls + [
        path('dashboard/', admin.site.admin_view(DashboardView.as_view()), name='admin_dashboard'),
    ]


# Patch the admin site URLs
admin.site.get_urls = lambda: get_admin_urls(admin.AdminSite.get_urls(admin.site))

# Option 2: Create a custom admin site (requires more changes elsewhere)
"""
# Uncomment and use this approach if you want a completely custom admin site
class DashboardAdminSite(admin.AdminSite):
    site_header = "Egypt Metro Administration"
    site_title = "Egypt Metro Admin Portal"
    index_title = "Welcome to Egypt Metro Admin Portal"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(DashboardView.as_view()), name='admin_dashboard'),
        ]
        return custom_urls + urls

# Replace the default admin site
admin_site = DashboardAdminSite(name='metro_admin')
# You would then need to register all models with this custom site
# And update urls.py to use admin_site.urls instead of admin.site.urls
"""
