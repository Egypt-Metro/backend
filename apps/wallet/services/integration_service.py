from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError

from .payment_service import PaymentService


class TicketIntegrationService:
    """Service for integrating wallet payments with tickets"""

    @staticmethod
    @transaction.atomic
    def purchase_ticket(user, ticket_type, quantity=1):
        """Purchase a ticket using the wallet"""
        from apps.tickets.constants.choices import TicketChoices
        from apps.tickets.services.ticket_service import TicketService

        # Get ticket price
        ticket_details = TicketChoices.TICKET_TYPES.get(ticket_type)
        if not ticket_details:
            raise ValidationError("Invalid ticket type")

        # Calculate total amount
        amount = Decimal(ticket_details['price']) * quantity

        # Process payment
        payment_result = PaymentService.process_payment(
            user=user,
            amount=amount,
            payment_type='TICKET_PURCHASE',
            description=f"Purchase of {quantity} {ticket_details['name']} ticket(s)"
        )

        if not payment_result['success']:
            return payment_result

        # Create the ticket(s) if payment was successful
        try:
            ticket_service = TicketService()
            tickets = ticket_service.create_ticket(
                user=user,
                ticket_type=ticket_type,
                quantity=quantity
            )

            # Update the transaction with the related object info
            transaction = payment_result['transaction']
            if isinstance(tickets, list):
                # Multiple tickets
                ticket_ids = [str(ticket.id) for ticket in tickets]
                transaction.related_object_type = 'tickets.Ticket'
                transaction.related_object_id = ','.join(ticket_ids)
            else:
                # Single ticket
                transaction.related_object_type = 'tickets.Ticket'
                transaction.related_object_id = str(tickets.id)

            transaction.save(update_fields=['related_object_type', 'related_object_id'])

            # Return success with created tickets
            return {
                'success': True,
                'tickets': tickets,
                'transaction': transaction,
                'message': f"Successfully purchased {quantity} ticket(s)",
                'new_balance': payment_result['new_balance']
            }
        except Exception as e:
            # If ticket creation fails, refund the payment
            refund_result = PaymentService.process_refund(payment_result['transaction'].id)

            return {
                'success': False,
                'message': f"Failed to create ticket: {str(e)}",
                'refund_processed': refund_result['success']
            }

    @staticmethod
    @transaction.atomic
    def upgrade_ticket(user, ticket_number, new_ticket_type):
        """Upgrade a ticket using the wallet"""
        from apps.tickets.constants.choices import TicketChoices
        from apps.tickets.services.ticket_service import TicketService
        from apps.tickets.models.ticket import Ticket

        try:
            # Find the ticket
            ticket = Ticket.objects.get(ticket_number=ticket_number, user=user)

            # Calculate upgrade cost
            old_ticket_details = TicketChoices.TICKET_TYPES.get(ticket.ticket_type)
            new_ticket_details = TicketChoices.TICKET_TYPES.get(new_ticket_type)

            if not old_ticket_details or not new_ticket_details:
                raise ValidationError("Invalid ticket type")

            upgrade_cost = Decimal(new_ticket_details['price']) - Decimal(old_ticket_details['price'])

            if upgrade_cost <= 0:
                raise ValidationError("New ticket type must be more expensive than current type")

            # Process payment
            payment_result = PaymentService.process_payment(
                user=user,
                amount=upgrade_cost,
                payment_type='TICKET_UPGRADE',
                related_object_type='tickets.Ticket',
                related_object_id=str(ticket.id),
                description=f"Upgrade ticket from {old_ticket_details['name']} to {new_ticket_details['name']}"
            )

            if not payment_result['success']:
                return payment_result

            # Upgrade the ticket if payment was successful
            ticket_service = TicketService()
            upgrade_result = ticket_service.upgrade_ticket(
                ticket_number=ticket_number,
                new_ticket_type=new_ticket_type,
                payment_confirmed=True
            )

            if upgrade_result[0]:  # Success flag from upgrade_ticket
                return {
                    'success': True,
                    'ticket': ticket,
                    'transaction': payment_result['transaction'],
                    'message': f"Successfully upgraded ticket to {new_ticket_details['name']}",
                    'new_balance': payment_result['new_balance']
                }
            else:
                # If ticket upgrade fails, refund the payment
                refund_result = PaymentService.process_refund(payment_result['transaction'].id)

                return {
                    'success': False,
                    'message': upgrade_result[1]['message'],  # Error message from upgrade_ticket
                    'refund_processed': refund_result['success']
                }

        except Ticket.DoesNotExist:
            return {
                'success': False,
                'message': "Ticket not found"
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to upgrade ticket: {str(e)}"
            }


class SubscriptionIntegrationService:
    """Service for integrating wallet payments with subscriptions"""

    @staticmethod
    @transaction.atomic
    def purchase_subscription(user, subscription_type, zones_count, start_station_id=None, end_station_id=None):
        """Purchase a subscription using the wallet"""
        from apps.tickets.constants.pricing import SubscriptionPricing
        from apps.tickets.services.subscription_service import SubscriptionService

        # Determine price based on type and zones
        if subscription_type == 'MONTHLY':
            price_category = SubscriptionService().get_price_category(zones_count)
            price = SubscriptionPricing.MONTHLY.get(price_category)
        elif subscription_type == 'QUARTERLY':
            price_category = SubscriptionService().get_price_category(zones_count)
            price = SubscriptionPricing.QUARTERLY.get(price_category)
        elif subscription_type == 'ANNUAL':
            price = SubscriptionPricing.ANNUAL['LINES_1_2'] if zones_count == 2 else SubscriptionPricing.ANNUAL['ALL_LINES']
        else:
            raise ValidationError("Invalid subscription type")

        if price is None:
            raise ValidationError("Invalid zones count for subscription type")

        amount = Decimal(price)

        # Process payment
        payment_result = PaymentService.process_payment(
            user=user,
            amount=amount,
            payment_type='SUBSCRIPTION_PURCHASE',
            description=f"Purchase of {subscription_type} subscription for {zones_count} zones"
        )

        if not payment_result['success']:
            return payment_result

        # Create the subscription if payment was successful
        try:
            subscription_service = SubscriptionService()
            subscription = subscription_service.create_subscription(
                user=user,
                subscription_type=subscription_type,
                zones_count=zones_count,
                payment_confirmed=True,
                start_station_id=start_station_id,
                end_station_id=end_station_id
            )

            # Update the transaction with the related object info
            transaction = payment_result['transaction']
            transaction.related_object_type = 'tickets.UserSubscription'
            transaction.related_object_id = str(subscription.id)
            transaction.save(update_fields=['related_object_type', 'related_object_id'])

            return {
                'success': True,
                'subscription': subscription,
                'transaction': transaction,
                'message': f"Successfully purchased {subscription_type} subscription",
                'new_balance': payment_result['new_balance']
            }
        except Exception as e:
            # If subscription creation fails, refund the payment
            refund_result = PaymentService.process_refund(payment_result['transaction'].id)

            return {
                'success': False,
                'message': f"Failed to create subscription: {str(e)}",
                'refund_processed': refund_result['success']
            }
