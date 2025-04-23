# apps/tickets/services/subscription_qr_service.py
import qrcode
import json
import hashlib
import logging
from typing import Dict, Tuple
from io import BytesIO
from base64 import b64encode
from django.utils import timezone
from django.conf import settings
from ..models.subscription import SubscriptionPlan

logger = logging.getLogger(__name__)


class SubscriptionQRService:
    """Service for handling QR code generation and validation for subscriptions"""

    QR_VERSION = 1
    QR_BOX_SIZE = 10
    QR_BORDER = 4
    QR_ERROR_CORRECTION = qrcode.constants.ERROR_CORRECT_H
    QR_VALIDITY_HOURS = 24  # QR codes are valid for 24 hours after generation
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, current_user=None):
        """
        Initialize QR service
        """
        self.current_user = current_user
        self.current_time = timezone.now()

    def generate_subscription_qr(self, subscription_data: Dict) -> Tuple[str, str]:
        """
        Generate QR code and validation hash for a subscription

        Args:
            subscription_data: Dictionary containing subscription information

        Returns:
            Tuple[str, str]: (qr_code_base64, validation_hash)
        """
        try:
            # Validate required fields
            required_fields = ['subscription_id', 'user_id', 'plan_type']
            if not all(field in subscription_data for field in required_fields):
                missing = [f for f in required_fields if f not in subscription_data]
                raise ValueError(f"Missing required subscription data: {', '.join(missing)}")

            # Add metadata with proper timezone handling
            current_time = self.current_time.strftime(self.DATE_FORMAT)
            username = getattr(self.current_user, 'username', 'system')

            validation_data = {
                'subscription_id': subscription_data['subscription_id'],
                'user_id': subscription_data['user_id'],
                'plan_type': subscription_data['plan_type'],
                'generated_at': current_time,
                'generated_by': username
            }

            # Generate validation hash
            validation_hash = self._generate_validation_hash(validation_data)

            # Prepare complete QR data
            qr_data = {
                **subscription_data,
                'generated_at': current_time,
                'generated_by': username,
                'validation_hash': validation_hash,
                'timezone': settings.TIME_ZONE,
                'qr_type': 'subscription'  # Add QR type to distinguish from other QR codes
            }

            # Generate QR code
            qr = qrcode.QRCode(
                version=self.QR_VERSION,
                error_correction=self.QR_ERROR_CORRECTION,
                box_size=self.QR_BOX_SIZE,
                border=self.QR_BORDER
            )
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)

            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_base64 = b64encode(buffer.getvalue()).decode()

            logger.info(
                f"Generated QR code for subscription {subscription_data['subscription_id']} "
                f"by user {username} at {current_time}"
            )
            return qr_base64, validation_hash

        except Exception as e:
            logger.error(f"Error generating QR code: {str(e)}")
            raise ValueError(f"Failed to generate QR code: {str(e)}")

    @classmethod
    def validate_qr(cls, qr_data: str, stored_hash: str) -> Tuple[bool, Dict]:
        """
        Validate QR code data against stored hash

        Args:
            qr_data: JSON string containing subscription data
            stored_hash: Previously generated validation hash

        Returns:
            Tuple[bool, Dict]: (is_valid, result_data)
        """
        try:
            # Parse QR data
            subscription_data = json.loads(qr_data)

            # Verify it's a subscription QR code
            if subscription_data.get('qr_type') != 'subscription':
                return False, {"error": "Invalid QR code type"}

            # Verify required fields
            required_fields = [
                'subscription_id', 'user_id', 'plan_type',
                'generated_at', 'validation_hash'
            ]
            if not all(field in subscription_data for field in required_fields):
                return False, {"error": "Invalid QR code format"}

            # Verify plan type
            valid_subscription_types = [choice[0] for choice in SubscriptionPlan.SUBSCRIPTION_TYPE_CHOICES]
            if subscription_data['plan_type'] not in valid_subscription_types:
                return False, {"error": "Invalid subscription type"}

            # Verify timestamp
            generated_at = timezone.datetime.strptime(
                subscription_data['generated_at'],
                cls.DATE_FORMAT
            )
            if timezone.now() - generated_at > timezone.timedelta(hours=cls.QR_VALIDITY_HOURS):
                return False, {"error": "QR code has expired"}

            # Regenerate and verify hash
            validation_data = {
                'subscription_id': subscription_data['subscription_id'],
                'user_id': subscription_data['user_id'],
                'plan_type': subscription_data['plan_type'],
                'generated_at': subscription_data['generated_at'],
                'generated_by': subscription_data.get('generated_by', 'system')
            }
            generated_hash = cls._generate_validation_hash(validation_data)

            if generated_hash != stored_hash:
                return False, {"error": "Invalid QR code"}

            return True, subscription_data

        except json.JSONDecodeError:
            return False, {"error": "Malformed QR code data"}
        except (KeyError, ValueError) as e:
            return False, {"error": f"Invalid QR code format: {str(e)}"}
        except Exception as e:
            logger.error(f"Error validating QR code: {str(e)}")
            return False, {"error": "QR code validation failed"}

    @staticmethod
    def _generate_validation_hash(data: Dict) -> str:
        """Generate validation hash for subscription data"""
        try:
            hash_input = (
                f"{data['subscription_id']}:"
                f"{data['user_id']}:"
                f"{data['plan_type']}:"
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
    def create_subscription_qr_data(cls, subscription) -> Dict:
        """Create standardized subscription data for QR code generation"""
        # Get the zones covered
        zones_covered = []
        if subscription.plan.zones:
            zones_covered = list(range(1, subscription.plan.zones + 1))
        elif subscription.plan.type == 'ANNUAL':
            lines = subscription.plan.lines or []
            if any('Third Line' in line for line in lines):
                zones_covered = list(range(1, 11))
            else:
                zones_covered = list(range(1, 10))

        return {
            'subscription_id': subscription.id,
            'user_id': subscription.user_id,
            'plan_type': subscription.plan.type,
            'plan_name': subscription.plan.name,
            'start_date': subscription.start_date.isoformat(),
            'end_date': subscription.end_date.isoformat(),
            'status': subscription.status,
            'stations': {
                'start': subscription.start_station.name if subscription.start_station else None,
                'end': subscription.end_station.name if subscription.end_station else None
            },
            'zones_covered': zones_covered,
            'plan_details': {
                'price': float(subscription.plan.price),
                'description': subscription.plan.description,
                'zones': subscription.plan.zones,
                'lines': subscription.plan.lines
            }
        }
