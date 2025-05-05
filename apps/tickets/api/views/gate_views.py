from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone

from apps.tickets.models.ticket import Ticket
from apps.tickets.services.validation_service import ValidationService
from apps.tickets.services.hardware_service import HardwareService


class GateStatusView(APIView):
    """
    API endpoint for hardware to get the latest validation result.
    Returns "1" if the ticket is valid, "0" if invalid.
    No parameters needed - returns the last validation result.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # Simply return the latest validation result
        hardware_service = HardwareService()
        result = hardware_service.get_latest_validation_result()
        return Response(result, content_type="text/plain")


class GateValidationView(APIView):
    """
    API endpoint to validate tickets and stations.
    This is used by the mobile app or web interface to validate tickets.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        ticket_number = request.query_params.get('ticket_number')
        station_id = request.query_params.get('station_id')

        # Return 0 if required parameters are missing
        if not ticket_number or not station_id:
            return Response("0", content_type="text/plain")

        try:
            # Convert station_id to integer
            station_id = int(station_id)

            # Get the ticket, if it exists
            ticket = Ticket.objects.get(ticket_number=ticket_number)

            # Check if ticket is expired
            if ticket.status == 'ACTIVE' and ticket.valid_until < timezone.now():
                return Response("0", content_type="text/plain")

            # Determine if entry or exit validation
            if ticket.status == 'ACTIVE' and not ticket.entry_station_id:
                # Entry validation
                result = ValidationService.validate_entry(ticket_number, station_id)
                return Response("1" if result.get('is_valid', False) else "0", content_type="text/plain")

            elif ticket.status == 'IN_USE' and not ticket.exit_station_id:
                # Exit validation
                result = ValidationService.validate_exit(ticket_number, station_id)
                return Response("1" if result.get('is_valid', False) else "0", content_type="text/plain")

            else:
                # Invalid ticket state
                return Response("0", content_type="text/plain")

        except (Ticket.DoesNotExist, ValueError):
            # Ticket doesn't exist or invalid station_id
            return Response("0", content_type="text/plain")
