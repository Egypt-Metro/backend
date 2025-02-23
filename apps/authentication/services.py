# authentication/services.py
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from datetime import timedelta
import logging

from .models import PasswordResetToken

logger = logging.getLogger(__name__)


class PasswordResetService:
    TOKEN_EXPIRY_HOURS = 24

    @staticmethod
    def create_reset_token(user):
        """Create a new password reset token"""
        # Invalidate any existing tokens
        PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)

        # Create new token
        token = PasswordResetToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=PasswordResetService.TOKEN_EXPIRY_HOURS)
        )
        return token

    @staticmethod
    def validate_token(token_str):
        """Validate a password reset token"""
        try:
            token = PasswordResetToken.objects.get(token=token_str, is_used=False)
            return token.is_valid()
        except PasswordResetToken.DoesNotExist:
            return False

    @staticmethod
    def get_valid_token(token_str):
        """Get a valid token object"""
        try:
            token = PasswordResetToken.objects.get(token=token_str, is_used=False)
            if token.is_valid():
                return token
            return None
        except PasswordResetToken.DoesNotExist:
            return None

    @staticmethod
    def send_reset_email(user, token):
        """Send password reset email"""
        try:
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token.token}"

            # Render email template
            context = {
                'user': user,
                'reset_url': reset_url,
                'expires_in': PasswordResetService.TOKEN_EXPIRY_HOURS
            }

            html_message = render_to_string('authentication/reset_password_email.html', context)
            plain_message = render_to_string('authentication/reset_password_email.txt', context)

            send_mail(
                subject='Reset Your Password',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message
            )
            
            logger.info(f"Password reset email sent to {user.email}")
            return True

        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
            return False

    @staticmethod
    def reset_password(token, new_password):
        """Reset user's password"""
        token_obj = PasswordResetService.get_valid_token(token)
        if not token_obj:
            return False

        try:
            user = token_obj.user
            user.set_password(new_password)
            user.save()

            # Mark token as used
            token_obj.is_used = True
            token_obj.save()

            logger.info(f"Password reset successful for user {user.email}")
            return True

        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            return False