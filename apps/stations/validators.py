# apps/stations/validators.py

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_coordinates(latitude: float, longitude: float) -> None:
    """Validates geographical coordinates."""
    if not -90 <= latitude <= 90:
        raise ValidationError(_('Latitude must be between -90 and 90 degrees.'))
    if not -180 <= longitude <= 180:
        raise ValidationError(_('Longitude must be between -180 and 180 degrees.'))


def validate_color_code(color_code: str) -> None:
    """Validates hex color code format."""
    if not color_code.startswith('#') or len(color_code) != 7:
        raise ValidationError(_('Color code must be in #RRGGBB format.'))
    try:
        int(color_code[1:], 16)
    except ValueError:
        raise ValidationError(_('Invalid hex color code.'))
