from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    def has_delete_permission(self, request, obj=None):
        return False  # Disable user deletion

admin.site.site_header = "Egypt Metro"
admin.site.site_title = "Egypt Metro Admin Portal"
admin.site.index_title = "Welcome to Egypt Metro Admin Portal"