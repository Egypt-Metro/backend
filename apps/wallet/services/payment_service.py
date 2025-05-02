from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError

from ..models.wallet import UserWallet
from ..models.transaction import Transaction
from .wallet_service import WalletService


class PaymentService:
    """Service for handling payments"""

    @staticmethod
    @transaction.atomic
    def process_payment(
        user,
        amount,
        payment_type,
        related_object_type=None,
        related_object_id=None,
        description=None
    ):
        """Process a payment from a user's wallet"""
        amount = Decimal(amount)
        if amount <= 0:
            raise ValidationError("Amount must be positive")

        try:
            wallet = UserWallet.objects.get(user=user)
        except UserWallet.DoesNotExist:
            wallet = WalletService.get_or_create_wallet(user)

        if wallet.balance < amount:
            return {
                'success': False,
                'message': "Insufficient funds in wallet",
                'requires_top_up': True,
                'amount_required': amount - wallet.balance
            }

        # Record the transaction
        transaction = Transaction.objects.create(
            user=user,
            wallet=wallet,
            amount=amount,
            type=payment_type,
            status='PENDING',
            related_object_type=related_object_type,
            related_object_id=related_object_id,
            description=description or f"Payment for {payment_type}"
        )

        try:
            # Process payment
            wallet.withdraw_funds(amount)

            # Update transaction status
            transaction.status = 'COMPLETED'
            transaction.save(update_fields=['status', 'updated_at'])

            return {
                'success': True,
                'wallet': wallet,
                'transaction': transaction,
                'message': f"Payment of {amount} EGP successful",
                'new_balance': wallet.balance
            }
        except Exception as e:
            # Handle failure
            transaction.status = 'FAILED'
            transaction.description = f"{transaction.description} - Error: {str(e)}"
            transaction.save(update_fields=['status', 'description', 'updated_at'])

            return {
                'success': False,
                'wallet': wallet,
                'transaction': transaction,
                'message': f"Payment failed: {str(e)}"
            }

    @staticmethod
    @transaction.atomic
    def process_refund(transaction_id):
        """Process a refund for a previous transaction"""
        try:
            original_transaction = Transaction.objects.get(id=transaction_id)
        except Transaction.DoesNotExist:
            raise ValidationError("Transaction not found")

        if original_transaction.status != 'COMPLETED':
            raise ValidationError("Cannot refund a transaction that is not completed")

        if original_transaction.type not in ['PAYMENT', 'TICKET_PURCHASE', 'SUBSCRIPTION_PURCHASE', 'TICKET_UPGRADE']:
            raise ValidationError("Can only refund payment transactions")

        wallet = original_transaction.wallet
        amount = original_transaction.amount
        user = original_transaction.user

        # Record the refund transaction
        refund_transaction = Transaction.objects.create(
            user=user,
            wallet=wallet,
            amount=amount,
            type='REFUND',
            status='PENDING',
            related_object_type=original_transaction.related_object_type,
            related_object_id=original_transaction.related_object_id,
            description=f"Refund for {original_transaction.id}"
        )

        try:
            # Process refund
            wallet.add_funds(amount)

            # Update transactions status
            refund_transaction.status = 'COMPLETED'
            refund_transaction.save(update_fields=['status', 'updated_at'])

            original_transaction.status = 'REFUNDED'
            original_transaction.save(update_fields=['status', 'updated_at'])

            return {
                'success': True,
                'wallet': wallet,
                'transaction': refund_transaction,
                'original_transaction': original_transaction,
                'message': f"Refund of {amount} EGP successful",
                'new_balance': wallet.balance
            }
        except Exception as e:
            # Handle failure
            refund_transaction.status = 'FAILED'
            refund_transaction.description = f"{refund_transaction.description} - Error: {str(e)}"
            refund_transaction.save(update_fields=['status', 'description', 'updated_at'])

            return {
                'success': False,
                'wallet': wallet,
                'transaction': refund_transaction,
                'message': f"Refund failed: {str(e)}"
            }
