# apps/users/services/profile_service.py
from django.core.cache import cache


class ProfileService:
    @staticmethod
    def update_profile(user, data):
        """Update user profile with cache invalidation"""
        try:
            for key, value in data.items():
                setattr(user, key, value)
            user.save()

            # Invalidate cache
            cache_key = f'user_profile_{user.id}'
            cache.delete(cache_key)

            return user
        except Exception as e:
            raise ValueError(f"Failed to update profile: {str(e)}")
