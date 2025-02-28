# apps/users/views/auth_test.py

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


@login_required
def test_auth(request):
    """Test authentication status."""
    return JsonResponse({
        'authenticated': True,
        'user': request.user.email,
        'is_superuser': request.user.is_superuser,
        'is_staff': request.user.is_staff
    })
