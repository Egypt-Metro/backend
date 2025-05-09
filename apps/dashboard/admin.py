from django.contrib import admin


# Admin customizations
admin.site.site_header = 'Egypt Metro Admin Portal'
admin.site.site_title = 'Metro Admin'
admin.site.index_title = 'Metro Administration'


# Add dashboard link directly to admin index
class MetroAdminSite(admin.AdminSite):
    def each_context(self, request):
        context = super().each_context(request)
        context['has_dashboard_access'] = True
        return context


# Keep the index template customization
admin.site.index_template = 'admin/index.html'
