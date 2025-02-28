# utils/helpers.py
from django.core.cache import cache
from django.contrib.auth.models import User


def get_cached_user_profile(user_id):
    cache_key = f'user_profile_{user_id}'
    profile = cache.get(cache_key)
    if not profile:
        profile = User.objects.get(id=user_id)
        cache.set(cache_key, profile, timeout=300)
    return profile
