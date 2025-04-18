import qrcode
import json
import hashlib
from typing import Dict
from base64 import b64encode
from io import BytesIO


def generate_ticket_qr(ticket_data: Dict) -> tuple:
    """
    Generate QR code for a ticket and its validation hash.

    Args:
        ticket_data: Dictionary containing ticket information:
            - id: Ticket ID
            - user_id: User ID
            - entry_station: Entry station name
            - ticket_number: Ticket number
            - created_at: Creation timestamp

    Returns:
        tuple: (qr_code_base64, validation_hash)
    """
    # Create a validation hash
    hash_data = (
        f"{ticket_data['ticket_number']}:{ticket_data['user_id']}:"
        f"{ticket_data['entry_station']}:{ticket_data['created_at']}"
    )
    validation_hash = hashlib.sha256(hash_data.encode()).hexdigest()

    # Add validation hash to ticket data
    ticket_data['validation_hash'] = validation_hash

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(json.dumps(ticket_data))
    qr.make(fit=True)

    # Create QR code image and convert to base64
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_base64 = b64encode(buffer.getvalue()).decode()

    return qr_base64, validation_hash
