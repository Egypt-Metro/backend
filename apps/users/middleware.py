# apps/users/middleware.py

from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class AdminAccessMiddleware(MiddlewareMixin):
    """
    Middleware to handle admin panel access control.

    This middleware:
    1. Ensures users are authenticated for admin access
    2. Verifies staff permissions
    3. Handles redirects and messages
    4. Logs access attempts
    """

    ADMIN_URLS = [
        '/admin/',
        '/admin/login/',
        '/admin/logout/',
    ]

    def process_request(self, request):
        """Process incoming requests."""
        try:
            # Skip middleware for non-admin URLs
            if not self._is_admin_url(request.path):
                return None

            # Allow access to login and logout pages
            if self._is_auth_url(request.path):
                return None

            # Check authentication
            if not request.user.is_authenticated:
                logger.warning(f"Unauthenticated access attempt to admin from IP: {self._get_client_ip(request)}")
                messages.warning(request, 'Please log in to access the admin panel.')
                return self._handle_redirect('admin:login')

            # Check staff permission
            if not request.user.is_staff:
                logger.warning(
                    f"Unauthorized admin access attempt by user: {request.user.email} "
                    f"from IP: {self._get_client_ip(request)}"
                )
                messages.error(request, 'You do not have permission to access the admin panel.')
                return self._handle_redirect('home')

            # Log successful access
            if settings.DEBUG:
                logger.info(f"Admin access by {request.user.email} to {request.path}")

        except Exception as e:
            logger.error(f"Error in AdminAccessMiddleware: {str(e)}")
            messages.error(request, 'An error occurred. Please try again.')
            return self._handle_redirect('home')

        return None

    def _is_admin_url(self, path: str) -> bool:
        """Check if the URL is an admin URL."""
        return any(path.startswith(url) for url in self.ADMIN_URLS)

    def _is_auth_url(self, path: str) -> bool:
        """Check if the URL is an authentication URL."""
        return path.startswith('/admin/login/') or path.startswith('/admin/logout/')

    def _get_client_ip(self, request) -> str:
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', '')

    def _handle_redirect(self, url_name: str):
        """Handle redirect with proper URL reverse."""
        try:
            return redirect(reverse(url_name))
        except Exception:
            return redirect('/')

    def process_response(self, request, response):
        """Process outgoing responses."""
        # Add security headers for admin pages
        if self._is_admin_url(request.path):
            response['X-Frame-Options'] = 'DENY'
            response['X-Content-Type-Options'] = 'nosniff'
            response['Referrer-Policy'] = 'same-origin'
        return response
