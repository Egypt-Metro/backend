from django.utils.translation import gettext_lazy as _


# Transaction type choices
class TransactionTypes:
    DEPOSIT = 'DEPOSIT'
    WITHDRAW = 'WITHDRAW'
    PAYMENT = 'PAYMENT'
    REFUND = 'REFUND'
    TICKET_PURCHASE = 'TICKET_PURCHASE'
    SUBSCRIPTION_PURCHASE = 'SUBSCRIPTION_PURCHASE'
    TICKET_UPGRADE = 'TICKET_UPGRADE'

    CHOICES = [
        (DEPOSIT, _('Deposit')),
        (WITHDRAW, _('Withdrawal')),
        (PAYMENT, _('Payment')),
        (REFUND, _('Refund')),
        (TICKET_PURCHASE, _('Ticket Purchase')),
        (SUBSCRIPTION_PURCHASE, _('Subscription Purchase')),
        (TICKET_UPGRADE, _('Ticket Upgrade')),
    ]


# Transaction status choices
class TransactionStatus:
    PENDING = 'PENDING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'
    REFUNDED = 'REFUNDED'

    CHOICES = [
        (PENDING, _('Pending')),
        (COMPLETED, _('Completed')),
        (FAILED, _('Failed')),
        (CANCELLED, _('Cancelled')),
        (REFUNDED, _('Refunded')),
    ]


# Payment method types
class PaymentMethodTypes:
    CREDIT_CARD = 'CREDIT_CARD'
    DEBIT_CARD = 'DEBIT_CARD'
    BANK_TRANSFER = 'BANK_TRANSFER'
    MOBILE_WALLET = 'MOBILE_WALLET'
    CASH = 'CASH'
    OTHER = 'OTHER'

    CHOICES = [
        (CREDIT_CARD, _('Credit Card')),
        (DEBIT_CARD, _('Debit Card')),
        (BANK_TRANSFER, _('Bank Transfer')),
        (MOBILE_WALLET, _('Mobile Wallet')),
        (CASH, _('Cash')),
        (OTHER, _('Other')),
    ]


# Payment gateway providers
class PaymentGateways:
    STRIPE = 'STRIPE'
    PAYPAL = 'PAYPAL'
    FAWRY = 'FAWRY'
    PAYMOB = 'PAYMOB'
    ACCEPT = 'ACCEPT'

    CHOICES = [
        (STRIPE, _('Stripe')),
        (PAYPAL, _('PayPal')),
        (FAWRY, _('Fawry')),
        (PAYMOB, _('PayMob')),
        (ACCEPT, _('Accept')),
    ]


# Transaction limits (in EGP)
class TransactionLimits:
    MIN_DEPOSIT = 5.0
    MAX_DEPOSIT = 5000.0
    MIN_WITHDRAW = 5.0
    MAX_WITHDRAW = 5000.0
    DAILY_LIMIT = 10000.0
    MONTHLY_LIMIT = 100000.0
