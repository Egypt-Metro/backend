import re
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from ..constants.choices import TransactionLimits


def validate_positive_amount(amount):
    """
    Validate that the amount is positive

    Args:
        amount: Amount to validate

    Raises:
        ValidationError: If amount is not positive
    """
    try:
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValidationError(_("Amount must be greater than zero."))
    except (TypeError, ValueError):
        raise ValidationError(_("Invalid amount format."))


def validate_transaction_limits(user, amount, transaction_type):
    """
    Validate transaction amount against defined limits

    Args:
        user: User model instance
        amount: Transaction amount
        transaction_type: Type of transaction

    Raises:
        ValidationError: If amount exceeds any limits
    """
    from ..models.transaction import Transaction
    from django.utils import timezone
    import datetime

    amount = Decimal(str(amount))

    # Check transaction-specific limits
    if transaction_type == 'DEPOSIT':
        if amount < TransactionLimits.MIN_DEPOSIT:
            raise ValidationError(
                _("Minimum deposit amount is {0} EGP.").format(TransactionLimits.MIN_DEPOSIT)
            )
        if amount > TransactionLimits.MAX_DEPOSIT:
            raise ValidationError(
                _("Maximum deposit amount is {0} EGP.").format(TransactionLimits.MAX_DEPOSIT)
            )

    elif transaction_type == 'WITHDRAW':
        if amount < TransactionLimits.MIN_WITHDRAW:
            raise ValidationError(
                _("Minimum withdrawal amount is {0} EGP.").format(TransactionLimits.MIN_WITHDRAW)
            )
        if amount > TransactionLimits.MAX_WITHDRAW:
            raise ValidationError(
                _("Maximum withdrawal amount is {0} EGP.").format(TransactionLimits.MAX_WITHDRAW)
            )

    # Check daily limit
    today = timezone.now().date()
    today_start = datetime.datetime.combine(today, datetime.time.min, tzinfo=timezone.utc)
    today_end = datetime.datetime.combine(today, datetime.time.max, tzinfo=timezone.utc)

    daily_transactions = Transaction.objects.filter(
        user=user,
        type=transaction_type,
        status='COMPLETED',
        created_at__range=(today_start, today_end)
    )

    daily_total = sum(t.amount for t in daily_transactions)

    if daily_total + amount > TransactionLimits.DAILY_LIMIT:
        raise ValidationError(
            _("This transaction would exceed your daily limit of {0} EGP.").format(
                TransactionLimits.DAILY_LIMIT
            )
        )

    # Check monthly limit
    month_start = datetime.datetime(today.year, today.month, 1, tzinfo=timezone.utc)
    month_end = today_end

    monthly_transactions = Transaction.objects.filter(
        user=user,
        type=transaction_type,
        status='COMPLETED',
        created_at__range=(month_start, month_end)
    )

    monthly_total = sum(t.amount for t in monthly_transactions)

    if monthly_total + amount > TransactionLimits.MONTHLY_LIMIT:
        raise ValidationError(
            _("This transaction would exceed your monthly limit of {0} EGP.").format(
                TransactionLimits.MONTHLY_LIMIT
            )
        )


def validate_card_number(card_number):
    """
    Validate credit card number using Luhn algorithm

    Args:
        card_number: Card number to validate (string)

    Raises:
        ValidationError: If card number is invalid
    """
    # Remove spaces and dashes
    card_number = re.sub(r'[\s-]', '', card_number)

    # Check if all characters are digits
    if not card_number.isdigit():
        raise ValidationError(_("Card number can only contain digits."))

    # Check length
    if len(card_number) < 13 or len(card_number) > 19:
        raise ValidationError(_("Card number length is invalid."))

    # Luhn algorithm
    digits = [int(d) for d in card_number]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(divmod(d * 2, 10))

    if checksum % 10 != 0:
        raise ValidationError(_("Invalid card number."))

    return True


def validate_card_expiry(month, year):
    """
    Validate that the card expiry date is in the future

    Args:
        month: Expiry month (1-12)
        year: Expiry year (full 4-digit year)

    Raises:
        ValidationError: If expiry date is invalid or in the past
    """
    from django.utils import timezone

    try:
        month = int(month)
        year = int(year)
    except (TypeError, ValueError):
        raise ValidationError(_("Invalid expiry date format."))

    if month < 1 or month > 12:
        raise ValidationError(_("Invalid month."))

    current_date = timezone.now().date()
    current_year = current_date.year
    current_month = current_date.month

    if year < current_year or (year == current_year and month < current_month):
        raise ValidationError(_("Card has expired."))

    return True


def validate_cvv(cvv):
    """
    Validate CVV/CVC code

    Args:
        cvv: CVV/CVC code

    Raises:
        ValidationError: If CVV/CVC is invalid
    """
    # Remove any spaces
    cvv = str(cvv).strip()

    # Check if all characters are digits
    if not cvv.isdigit():
        raise ValidationError(_("CVV can only contain digits."))

    # Check length (3-4 digits)
    if len(cvv) < 3 or len(cvv) > 4:
        raise ValidationError(_("CVV must be 3 or 4 digits."))

    return True
