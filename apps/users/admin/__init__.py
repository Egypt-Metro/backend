from django.contrib import admin
from django.contrib.auth import get_user_model
from .user_admin import UserAdmin

User = get_user_model()

# Register the User model with the custom admin
admin.site.register(User, UserAdmin)

# Admin site customization
admin.site.site_header = "Egypt Metro Administration"
admin.site.site_title = "Egypt Metro Admin Portal"
admin.site.index_title = "Welcome to Egypt Metro Admin Portal"
