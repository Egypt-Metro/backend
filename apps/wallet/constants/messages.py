from django.utils.translation import gettext_lazy as _


# Success messages
class SuccessMessages:
    WALLET_CREATED = _("Wallet successfully created.")
    FUNDS_ADDED = _("Funds successfully added to your wallet.")
    FUNDS_WITHDRAWN = _("Funds successfully withdrawn from your wallet.")
    PAYMENT_COMPLETED = _("Payment completed successfully.")
    TICKET_PURCHASED = _("Ticket purchased successfully.")
    SUBSCRIPTION_PURCHASED = _("Subscription purchased successfully.")
    TICKET_UPGRADED = _("Ticket upgraded successfully.")
    REFUND_PROCESSED = _("Refund processed successfully.")
    PAYMENT_METHOD_ADDED = _("Payment method added successfully.")
    PAYMENT_METHOD_UPDATED = _("Payment method updated successfully.")
    PAYMENT_METHOD_REMOVED = _("Payment method removed successfully.")
    DEFAULT_PAYMENT_METHOD_SET = _("Default payment method updated successfully.")


# Error messages
class ErrorMessages:
    WALLET_NOT_FOUND = _("Wallet not found.")
    INSUFFICIENT_FUNDS = _("Insufficient funds in wallet.")
    INVALID_AMOUNT = _("Invalid amount. Amount must be positive.")
    PAYMENT_METHOD_NOT_FOUND = _("Payment method not found.")
    PAYMENT_GATEWAY_ERROR = _("Payment gateway error: {0}")
    TRANSACTION_FAILED = _("Transaction failed: {0}")
    TRANSACTION_NOT_FOUND = _("Transaction not found.")
    INVALID_TRANSACTION_TYPE = _("Invalid transaction type.")
    INVALID_TRANSACTION_STATUS = _("Invalid transaction status.")
    MAXIMUM_WITHDRAWAL_LIMIT_EXCEEDED = _("Maximum withdrawal limit exceeded.")
    MAXIMUM_DEPOSIT_LIMIT_EXCEEDED = _("Maximum deposit limit exceeded.")
    DAILY_LIMIT_EXCEEDED = _("Daily transaction limit exceeded.")
    MONTHLY_LIMIT_EXCEEDED = _("Monthly transaction limit exceeded.")
    CANNOT_REMOVE_DEFAULT_PAYMENT_METHOD = _("Cannot remove the default payment method. Please set another payment method as default first.")


# Information messages
class InfoMessages:
    LOW_BALANCE = _("Your wallet balance is low: {0} EGP.")
    BALANCE_UPDATED = _("Your wallet balance has been updated: {0} EGP.")
    TRANSACTION_STATUS_UPDATED = _("Transaction status updated to: {0}.")
    PAYMENT_PENDING = _("Your payment is being processed.")
    PAYMENT_REQUIRES_AUTHENTICATION = _("Your payment requires additional authentication.")
    VERIFY_PAYMENT_METHOD = _("Please verify your payment method.")
    TRANSACTION_LIMIT_WARNING = _("You are approaching your transaction limit.")


# Notification messages
class NotificationMessages:
    FUNDS_ADDED_SUBJECT = _("Funds Added to Your Wallet")
    FUNDS_ADDED_BODY = _("You have successfully added {0} EGP to your wallet. Your current balance is {1} EGP.")

    FUNDS_WITHDRAWN_SUBJECT = _("Funds Withdrawn from Your Wallet")
    FUNDS_WITHDRAWN_BODY = _("You have withdrawn {0} EGP from your wallet. Your current balance is {1} EGP.")

    PAYMENT_COMPLETED_SUBJECT = _("Payment Completed")
    PAYMENT_COMPLETED_BODY = _("Your payment of {0} EGP has been completed successfully. Transaction reference: {1}")

    TICKET_PURCHASED_SUBJECT = _("Ticket Purchase Confirmation")
    TICKET_PURCHASED_BODY = _("You have successfully purchased {0} ticket(s). Your current wallet balance is {1} EGP.")

    SUBSCRIPTION_PURCHASED_SUBJECT = _("Subscription Purchase Confirmation")
    SUBSCRIPTION_PURCHASED_BODY = _("You have successfully purchased a {0} subscription. Your current wallet balance is {1} EGP.")

    REFUND_PROCESSED_SUBJECT = _("Refund Processed")
    REFUND_PROCESSED_BODY = _("Your refund of {0} EGP has been processed successfully. Your current wallet balance is {1} EGP.")

    LOW_BALANCE_SUBJECT = _("Low Wallet Balance")
    LOW_BALANCE_BODY = _("Your wallet balance is low: {0} EGP. Consider adding more funds to continue using our services.")
