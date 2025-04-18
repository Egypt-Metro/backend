import qrcode
import json
import hashlib
import logging
from typing import Dict, Tuple
from io import BytesIO
from base64 import b64encode
from django.utils import timezone
from ..constants.choices import TicketChoices

logger = logging.getLogger(__name__)


class QRService:
    """Service for handling QR code generation and validation for tickets"""

    QR_VERSION = 1
    QR_BOX_SIZE = 10
    QR_BORDER = 4
    QR_ERROR_CORRECTION = qrcode.constants.ERROR_CORRECT_H
    QR_VALIDITY_DAYS = 1

    @classmethod
    def generate_ticket_qr(cls, ticket_data: Dict) -> Tuple[str, str]:
        """
        Generate QR code and validation hash for a ticket

        Args:
            ticket_data: Dictionary containing:
                - ticket_number: Unique ticket identifier
                - user_id: ID of the ticket owner
                - ticket_type: Type of ticket (BASIC, STANDARD, etc.)
                - price_category: Ticket price category
                - max_stations: Maximum allowed stations
                - color: Ticket color
                - status: Current ticket status
                - entry_station: Entry station name (optional)
                - exit_station: Exit station name (optional)
                - valid_until: Ticket validity timestamp

        Returns:
            Tuple[str, str]: (qr_code_base64, validation_hash)

        Raises:
            ValueError: If required ticket data is missing
        """
        try:
            # Validate required fields
            required_fields = ['ticket_number', 'user_id', 'ticket_type', 'valid_until']
            if not all(field in ticket_data for field in required_fields):
                missing = [f for f in required_fields if f not in ticket_data]
                raise ValueError(f"Missing required ticket data: {', '.join(missing)}")

            # Add metadata
            validation_data = {
                'ticket_number': ticket_data['ticket_number'],
                'user_id': ticket_data['user_id'],
                'ticket_type': ticket_data['ticket_type'],
                'valid_until': ticket_data['valid_until'],
                'generated_at': cls.CURRENT_TIME,
                'generated_by': cls.CURRENT_USER
            }

            # Generate validation hash
            validation_hash = cls._generate_validation_hash(validation_data)

            # Prepare complete QR data
            qr_data = {
                **ticket_data,
                **validation_data,
                'validation_hash': validation_hash,
                'ticket_details': TicketChoices.TICKET_TYPES[ticket_data['ticket_type']]
            }

            # Generate QR code
            qr = qrcode.QRCode(
                version=cls.QR_VERSION,
                error_correction=cls.QR_ERROR_CORRECTION,
                box_size=cls.QR_BOX_SIZE,
                border=cls.QR_BORDER
            )
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)

            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_base64 = b64encode(buffer.getvalue()).decode()

            logger.info(f"Generated QR code for ticket {ticket_data['ticket_number']}")
            return qr_base64, validation_hash

        except Exception as e:
            logger.error(f"Error generating QR code: {str(e)}")
            raise ValueError(f"Failed to generate QR code: {str(e)}")

    @classmethod
    def validate_qr(cls, qr_data: str, stored_hash: str) -> Tuple[bool, Dict]:
        """
        Validate QR code data against stored hash

        Args:
            qr_data: JSON string containing ticket data
            stored_hash: Previously generated validation hash

        Returns:
            Tuple[bool, Dict]: (is_valid, result_data)
        """
        try:
            # Parse QR data
            ticket_data = json.loads(qr_data)

            # Verify required fields
            required_fields = [
                'ticket_number', 'user_id', 'ticket_type',
                'valid_until', 'generated_at', 'validation_hash'
            ]
            if not all(field in ticket_data for field in required_fields):
                return False, {"error": "Invalid QR code format"}

            # Verify ticket type
            if ticket_data['ticket_type'] not in TicketChoices.TICKET_TYPES:
                return False, {"error": "Invalid ticket type"}

            # Verify timestamp
            generated_at = timezone.datetime.strptime(
                ticket_data['generated_at'],
                "%Y-%m-%d %H:%M:%S"
            )
            if timezone.now() - generated_at > timezone.timedelta(days=cls.QR_VALIDITY_DAYS):
                return False, {"error": "QR code has expired"}

            # Regenerate and verify hash
            validation_data = {
                'ticket_number': ticket_data['ticket_number'],
                'user_id': ticket_data['user_id'],
                'ticket_type': ticket_data['ticket_type'],
                'valid_until': ticket_data['valid_until'],
                'generated_at': ticket_data['generated_at'],
                'generated_by': ticket_data.get('generated_by', cls.CURRENT_USER)
            }
            generated_hash = cls._generate_validation_hash(validation_data)

            if generated_hash != stored_hash:
                return False, {"error": "Invalid QR code"}

            return True, ticket_data

        except json.JSONDecodeError:
            return False, {"error": "Malformed QR code data"}
        except (KeyError, ValueError) as e:
            return False, {"error": f"Invalid QR code format: {str(e)}"}
        except Exception as e:
            logger.error(f"Error validating QR code: {str(e)}")
            return False, {"error": "QR code validation failed"}

    @classmethod
    def _generate_validation_hash(cls, data: Dict) -> str:
        """
        Generate validation hash for ticket data
        Uses SHA256 with ticket data and metadata
        """
        try:
            hash_input = (
                f"{data['ticket_number']}:"
                f"{data['user_id']}:"
                f"{data['ticket_type']}:"
                f"{data['valid_until']}:"
                f"{data['generated_at']}:"
                f"{data['generated_by']}"
            )
            return hashlib.sha256(hash_input.encode()).hexdigest()
        except KeyError as e:
            raise ValueError(f"Missing required field for hash generation: {str(e)}")

    @staticmethod
    def get_qr_image_url(qr_code_base64: str) -> str:
        """Get data URL for QR code image"""
        if not qr_code_base64:
            return ''
        return f"data:image/png;base64,{qr_code_base64}"

    @classmethod
    def create_ticket_qr_data(cls, ticket) -> Dict:
        """Create standardized ticket data for QR code generation"""
        ticket_type_details = TicketChoices.TICKET_TYPES[ticket.ticket_type]

        return {
            'ticket_number': ticket.ticket_number,
            'user_id': ticket.user_id,
            'ticket_type': ticket.ticket_type,
            'price_category': ticket.price_category,
            'max_stations': ticket.max_stations,
            'color': ticket.color,
            'status': ticket.status,
            'entry_station': ticket.entry_station.name if ticket.entry_station else None,
            'exit_station': ticket.exit_station.name if ticket.exit_station else None,
            'valid_until': ticket.valid_until.isoformat(),
            'ticket_details': {
                'name': ticket_type_details['name'],
                'description': ticket_type_details['description'],
                'price': float(ticket.price)
            }
        }
