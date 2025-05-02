import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from ..constants.messages import NotificationMessages

logger = logging.getLogger(__name__)


def send_email_notification(user, subject, message_body, template=None, context=None):
    """
    Send email notification to a user

    Args:
        user: User model instance
        subject: Email subject
        message_body: Plain text message
        template: Optional HTML template path
        context: Optional context for the template

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not user.email:
        logger.warning(f"Cannot send email to user {user.username}: No email address")
        return False

    try:
        html_message = None
        if template:
            html_message = render_to_string(template, context or {})

        send_mail(
            subject=subject,
            message=message_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {user.email}: {str(e)}")
        return False


def send_transaction_notification(transaction, notification_type):
    """
    Send transaction notification based on type

    Args:
        transaction: Transaction model instance
        notification_type: Type of notification to send

    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    user = transaction.user
    wallet = transaction.wallet

    if notification_type == 'funds_added':
        subject = NotificationMessages.FUNDS_ADDED_SUBJECT
        message = NotificationMessages.FUNDS_ADDED_BODY.format(
            transaction.amount, wallet.balance
        )
        template = 'wallet/emails/funds_added.html'

    elif notification_type == 'funds_withdrawn':
        subject = NotificationMessages.FUNDS_WITHDRAWN_SUBJECT
        message = NotificationMessages.FUNDS_WITHDRAWN_BODY.format(
            transaction.amount, wallet.balance
        )
        template = 'wallet/emails/funds_withdrawn.html'

    elif notification_type == 'payment_completed':
        subject = NotificationMessages.PAYMENT_COMPLETED_SUBJECT
        message = NotificationMessages.PAYMENT_COMPLETED_BODY.format(
            transaction.amount, transaction.id
        )
        template = 'wallet/emails/payment_completed.html'

    elif notification_type == 'ticket_purchased':
        subject = NotificationMessages.TICKET_PURCHASED_SUBJECT
        message = NotificationMessages.TICKET_PURCHASED_BODY.format(
            transaction.description, wallet.balance
        )
        template = 'wallet/emails/ticket_purchased.html'

    elif notification_type == 'subscription_purchased':
        subject = NotificationMessages.SUBSCRIPTION_PURCHASED_SUBJECT
        message = NotificationMessages.SUBSCRIPTION_PURCHASED_BODY.format(
            transaction.description, wallet.balance
        )
        template = 'wallet/emails/subscription_purchased.html'

    elif notification_type == 'refund_processed':
        subject = NotificationMessages.REFUND_PROCESSED_SUBJECT
        message = NotificationMessages.REFUND_PROCESSED_BODY.format(
            transaction.amount, wallet.balance
        )
        template = 'wallet/emails/refund_processed.html'

    else:
        logger.error(f"Unknown notification type: {notification_type}")
        return False

    # Prepare context for HTML template
    context = {
        'user': user,
        'transaction': transaction,
        'wallet': wallet
    }

    return send_email_notification(user, subject, message, template, context)


def send_low_balance_notification(user, balance, threshold=20.0):
    """
    Send notification when wallet balance is low

    Args:
        user: User model instance
        balance: Current wallet balance
        threshold: Balance threshold for notification

    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    if balance > threshold:
        return False

    subject = NotificationMessages.LOW_BALANCE_SUBJECT
    message = NotificationMessages.LOW_BALANCE_BODY.format(balance)
    template = 'wallet/emails/low_balance.html'

    context = {
        'user': user,
        'balance': balance,
        'threshold': threshold
    }

    return send_email_notification(user, subject, message, template, context)


def send_push_notification(user, title, body, data=None):
    """
    Send push notification to user's mobile device

    Args:
        user: User model instance
        title: Notification title
        body: Notification body
        data: Additional data for the notification

    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    # TODO: Implement push notification using Firebase Cloud Messaging or similar service
    # This is a placeholder for future implementation
    logger.info(f"Push notification for {user.username}: {title}")
    return True
