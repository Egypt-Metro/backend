from decimal import Decimal
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from ..models.wallet import UserWallet
from ..models.transaction import Transaction

User = get_user_model()


class WalletService:
    """Service for handling wallet operations"""

    @staticmethod
    def get_or_create_wallet(user):
        """Get or create a wallet for a user"""
        wallet, created = UserWallet.objects.get_or_create(user=user)
        return wallet

    @staticmethod
    @transaction.atomic
    def add_funds(user, amount, payment_method=None, reference=None, description=None):
        """Add funds to a user's wallet"""
        amount = Decimal(amount)
        if amount <= 0:
            raise ValidationError("Amount must be positive")

        wallet = WalletService.get_or_create_wallet(user)

        # Record the transaction
        transaction = Transaction.objects.create(
            user=user,
            wallet=wallet,
            amount=amount,
            type='DEPOSIT',
            status='PENDING',
            payment_method=payment_method,
            reference_number=reference or '',
            description=description or f"Added {amount} EGP to wallet"
        )

        try:
            # Process payment (in a real implementation, this would involve payment gateway)
            # This is a simplified version
            wallet.add_funds(amount)

            # Update transaction status
            transaction.status = 'COMPLETED'
            transaction.save(update_fields=['status', 'updated_at'])

            return {
                'success': True,
                'wallet': wallet,
                'transaction': transaction,
                'message': f"Successfully added {amount} EGP to wallet"
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
                'message': f"Failed to add funds: {str(e)}"
            }

    @staticmethod
    @transaction.atomic
    def withdraw_funds(user, amount, description=None):
        """Withdraw funds from a user's wallet"""
        amount = Decimal(amount)
        if amount <= 0:
            raise ValidationError("Amount must be positive")

        try:
            wallet = UserWallet.objects.get(user=user)
        except UserWallet.DoesNotExist:
            raise ValidationError("User wallet does not exist")

        if wallet.balance < amount:
            raise ValidationError("Insufficient funds")

        # Record the transaction
        transaction = Transaction.objects.create(
            user=user,
            wallet=wallet,
            amount=amount,
            type='WITHDRAW',
            status='PENDING',
            description=description or f"Withdrew {amount} EGP from wallet"
        )

        try:
            # Process withdrawal
            wallet.withdraw_funds(amount)

            # Update transaction status
            transaction.status = 'COMPLETED'
            transaction.save(update_fields=['status', 'updated_at'])

            return {
                'success': True,
                'wallet': wallet,
                'transaction': transaction,
                'message': f"Successfully withdrew {amount} EGP from wallet"
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
                'message': f"Failed to withdraw funds: {str(e)}"
            }

    @staticmethod
    def get_wallet_balance(user):
        """Get a user's wallet balance"""
        try:
            wallet = UserWallet.objects.get(user=user)
            return wallet.balance
        except UserWallet.DoesNotExist:
            # Create wallet if it doesn't exist
            wallet = UserWallet.objects.create(user=user)
            return wallet.balance

    @staticmethod
    def get_transaction_history(user, transaction_type=None, status=None, start_date=None, end_date=None, limit=None):
        """Get a user's transaction history with optional filters"""
        queryset = Transaction.objects.filter(user=user)

        if transaction_type:
            queryset = queryset.filter(type=transaction_type)

        if status:
            queryset = queryset.filter(status=status)

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        queryset = queryset.order_by('-created_at')

        if limit:
            queryset = queryset[:limit]

        return queryset
