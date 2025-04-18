import qrcode
import json
import hashlib
from typing import Dict, Tuple
from io import BytesIO
from base64 import b64encode
from django.utils import timezone


class QRService:
    @staticmethod
    def generate_ticket_qr(ticket_data: Dict) -> Tuple[str, str]:
        """
        Generate QR code and validation hash for a ticket

        Args:
            ticket_data: Dictionary containing ticket information:
                - ticket_number: Unique ticket identifier
                - user_id: ID of the ticket owner
                - entry_station: Entry station name
                - exit_station: Exit station name (optional)
                - price_category: Ticket price category
                - valid_until: Ticket validity timestamp

        Returns:
            tuple: (qr_code_base64, validation_hash)
        """
        # Add timestamp to ticket data
        ticket_data['generated_at'] = timezone.now().isoformat()

        # Generate validation hash
        validation_hash = QRService._generate_validation_hash(ticket_data)

        # Add validation hash to ticket data
        ticket_data['validation_hash'] = validation_hash

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )
        qr.add_data(json.dumps(ticket_data))
        qr.make(fit=True)

        # Create QR code image and convert to base64
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_base64 = b64encode(buffer.getvalue()).decode()

        return qr_base64, validation_hash

    @staticmethod
    def _generate_validation_hash(ticket_data: Dict) -> str:
        """
        Generate validation hash for ticket data
        Uses a combination of ticket number, user ID, station, and timestamp
        """
        hash_input = (
            f"{ticket_data['ticket_number']}:"
            f"{ticket_data['user_id']}:"
            f"{ticket_data['entry_station']}:"
            f"{ticket_data['generated_at']}"
        )
        return hashlib.sha256(hash_input.encode()).hexdigest()

    @staticmethod
    def validate_qr(qr_data: str, stored_hash: str) -> Tuple[bool, Dict]:
        """
        Validate QR code data against stored hash

        Args:
            qr_data: JSON string containing ticket data
            stored_hash: Previously generated validation hash

        Returns:
            tuple: (is_valid: bool, ticket_data: Dict)
        """
        try:
            # Parse QR data
            ticket_data = json.loads(qr_data)

            # Verify timestamp hasn't been tampered with
            generated_at = timezone.datetime.fromisoformat(ticket_data['generated_at'])
            if timezone.now() - generated_at > timezone.timedelta(days=1):
                return False, {"error": "QR code has expired"}

            # Regenerate hash and compare
            generated_hash = QRService._generate_validation_hash(ticket_data)
            if generated_hash != stored_hash:
                return False, {"error": "Invalid QR code"}

            return True, ticket_data

        except (json.JSONDecodeError, KeyError, ValueError):
            return False, {"error": "Malformed QR code"}

    @staticmethod
    def get_qr_image_url(qr_code_base64: str) -> str:
        """
        Get data URL for QR code image

        Args:
            qr_code_base64: Base64 encoded QR code image

        Returns:
            str: Data URL for the QR code image
        """
        return f"data:image/png;base64,{qr_code_base64}"

    @staticmethod
    def create_ticket_qr_data(ticket) -> Dict:
        """
        Create standardized ticket data for QR code generation

        Args:
            ticket: Ticket model instance

        Returns:
            Dict: Structured ticket data for QR code
        """
        return {
            'ticket_number': ticket.ticket_number,
            'user_id': ticket.user_id,
            'entry_station': ticket.entry_station.name,
            'exit_station': ticket.exit_station.name if ticket.exit_station else None,
            'price_category': ticket.price_category,
            'valid_until': ticket.valid_until.isoformat(),
            'status': ticket.status
        }
