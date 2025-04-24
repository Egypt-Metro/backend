import qrcode
import json
import hashlib
import logging
from typing import Dict, Tuple
from io import BytesIO
from base64 import b64encode
from django.utils import timezone
from ..constants.choices import TicketChoices
from django.conf import settings


logger = logging.getLogger(__name__)


class QRService:
    """Service for handling QR code generation and validation for tickets"""

    QR_VERSION = 4
    QR_BOX_SIZE = 10
    QR_BORDER = 4
    QR_ERROR_CORRECTION = qrcode.constants.ERROR_CORRECT_H
    QR_VALIDITY_DAYS = 1
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, current_user=None):
        """
        Initialize QR service
        """
        self.current_user = current_user
        self.current_time = timezone.now()

    def generate_ticket_qr(self, ticket_data: Dict) -> Tuple[str, str]:
        """
        Generate QR code and validation hash for a ticket with proper JWT implementation
        """
        try:
            # Validate required fields
            required_fields = ['ticket_number', 'user_id', 'ticket_type']
            if not all(field in ticket_data for field in required_fields):
                missing = [f for f in required_fields if f not in ticket_data]
                raise ValueError(f"Missing required ticket data: {', '.join(missing)}")

            # Import necessary modules
            from rest_framework_simplejwt.tokens import RefreshToken
            from django.contrib.auth import get_user_model
            from datetime import timedelta

            User = get_user_model()
            user_id = ticket_data['user_id']

            logger.info(f"Attempting to generate JWT for user_id: {user_id}")

            try:
                user = User.objects.get(id=user_id)

                # Create a refresh token for the user
                refresh = RefreshToken.for_user(user)

                # Customize the token with ticket-specific claims for better security
                refresh.payload.update({
                    'ticket_number': ticket_data['ticket_number'],
                    'ticket_type': ticket_data['ticket_type'],
                    'qr_purpose': 'metro_ticket_validation'
                })

                # Set token expiry to match the ticket validity period
                refresh.access_token.set_exp(lifetime=timedelta(days=1))

                # Get the access token as a string
                access_token = str(refresh.access_token)

                # Basic validation of token format
                if not (access_token.startswith('ey') and access_token.count('.') == 2):
                    logger.error(f"Generated token does not match JWT format: {access_token[:10]}...")
                    raise ValueError("Generated token is not in valid JWT format")

                logger.info(f"Valid JWT token generated for user {user_id}, token length: {len(access_token)}")

            except User.DoesNotExist:
                logger.error(f"User {user_id} not found")
                raise ValueError(f"User with ID {user_id} does not exist")

            except Exception as token_error:
                logger.error(f"Failed to generate JWT token: {str(token_error)}", exc_info=True)
                raise ValueError(f"JWT token generation failed: {str(token_error)}")

            # Add metadata
            current_time = self.current_time.strftime(self.DATE_FORMAT)
            username = getattr(self.current_user, 'username', 'system')

            # Prepare validation data
            validation_data = {
                'ticket_number': ticket_data['ticket_number'],
                'user_id': ticket_data['user_id'],
                'ticket_type': ticket_data['ticket_type'],
                'generated_at': current_time,
                'generated_by': username
            }

            # Generate validation hash
            validation_hash = self._generate_validation_hash(validation_data)

            # Prepare QR data with JWT token
            qr_data = {
                **ticket_data,
                'generated_at': current_time,
                'generated_by': username,
                'validation_hash': validation_hash,
                'timezone': settings.TIME_ZONE,
                'auth_token': access_token,  # Store the full JWT token
                'token_type': 'JWT'  # Explicitly indicate token type
            }

            # Log info about QR data
            logger.info(f"QR data prepared with fields: {list(qr_data.keys())}")
            logger.info(f"JWT token included (length: {len(access_token)})")

            # Generate QR code - possibly increase version if data is large
            qr_json = json.dumps(qr_data)
            json_size = len(qr_json)

            # Check if we need to adjust QR code version based on data size
            qr_version = self.QR_VERSION
            if json_size > 800:  # Version 4 limit with high error correction
                qr_version = 6  # Increase to version 6 for larger data
                logger.warning(f"Increasing QR version to 6 due to large data size ({json_size} bytes)")

            qr = qrcode.QRCode(
                version=qr_version,
                error_correction=self.QR_ERROR_CORRECTION,
                box_size=self.QR_BOX_SIZE,
                border=self.QR_BORDER
            )

            qr.add_data(qr_json)
            qr.make(fit=True)

            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_base64 = b64encode(buffer.getvalue()).decode()

            logger.info(f"QR code successfully generated for ticket {ticket_data['ticket_number']}")
            return qr_base64, validation_hash

        except Exception as e:
            logger.error(f"QR code generation failed: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to generate QR code: {str(e)}")

    @classmethod
    def validate_qr(cls, qr_data: str, stored_hash: str) -> Tuple[bool, Dict]:
        """
        Validate QR code data against stored hash
        """
        try:
            # Parse QR data
            ticket_data = json.loads(qr_data)

            # Verify required fields
            required_fields = [
                'ticket_number', 'user_id', 'ticket_type',
                'generated_at', 'validation_hash'
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
                'generated_at': ticket_data['generated_at'],
                'generated_by': ticket_data.get('generated_by', 'system')
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

    @staticmethod
    def _generate_validation_hash(data: Dict) -> str:
        """Generate validation hash for ticket data"""
        try:
            hash_input = (
                f"{data['ticket_number']}:"
                f"{data['user_id']}:"
                f"{data['ticket_type']}:"
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
