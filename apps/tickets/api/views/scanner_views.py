# apps/tickets/api/views/scanner_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone

from ...authentication import ScannerAPIKeyAuthentication
from ...models.ticket import Ticket
from ...permissions import IsAuthenticatedOrScanner
from apps.stations.models import Station


class ScannerProcessView(APIView):
    """API endpoint for scanners to process tickets (entry/exit)"""
    authentication_classes = [ScannerAPIKeyAuthentication]
    permission_classes = [IsAuthenticatedOrScanner]

    @transaction.atomic
    def post(self, request, format=None):
        ticket_number = request.data.get('ticket_number')
        station_id = request.data.get('station_id')

        # Basic validation
        if not ticket_number or not station_id:
            return Response(
                {'error': 'Ticket number and station ID are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Validate station exists
            try:
                station = Station.objects.get(id=station_id)
            except Station.DoesNotExist:
                return Response(
                    {'error': 'Invalid station ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get ticket with select_for_update to prevent race conditions
            ticket = Ticket.objects.select_for_update().get(ticket_number=ticket_number)

            # Check expiration
            if ticket.valid_until < timezone.now() and ticket.status == 'ACTIVE':
                ticket.status = 'EXPIRED'
                ticket.save(update_fields=['status'])
                return Response({
                    'is_valid': False,
                    'message': 'Ticket has expired'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Process based on ticket status
            if ticket.status == 'ACTIVE':
                # ENTRY
                ticket.entry_station_id = station_id
                ticket.entry_time = timezone.now()
                ticket.status = 'IN_USE'
                ticket.save(update_fields=['entry_station_id', 'entry_time', 'status'])

                return Response({
                    'is_valid': True,
                    'message': 'Entry authorized',
                    'scan_type': 'ENTRY',
                    'ticket_number': ticket.ticket_number,
                    'station_name': station.name,
                    'entry_time': ticket.entry_time
                })

            elif ticket.status == 'IN_USE':
                # EXIT
                ticket.exit_station_id = station_id
                ticket.exit_time = timezone.now()
                ticket.status = 'USED'
                ticket.save(update_fields=['exit_station_id', 'exit_time', 'status'])

                return Response({
                    'is_valid': True,
                    'message': 'Exit authorized',
                    'scan_type': 'EXIT',
                    'ticket_number': ticket.ticket_number,
                    'station_name': station.name,
                    'exit_time': ticket.exit_time
                })

            else:
                return Response({
                    'is_valid': False,
                    'message': f'Ticket is in invalid state for scanning: {ticket.status}'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Ticket.DoesNotExist:
            return Response({
                'is_valid': False,
                'message': 'Invalid ticket'
            }, status=status.HTTP_404_NOT_FOUND)
