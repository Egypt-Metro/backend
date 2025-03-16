# apps/trains/utils/file_validator.py
import os
import logging
from typing import Tuple, Optional, Union
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)


class FileValidator:
    """
    Comprehensive file validation utility with multiple detection methods
    """
    # Allowed MIME types with their corresponding extensions
    ALLOWED_MIME_TYPES = {
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/png': ['.png'],
        'image/gif': ['.gif'],
        'application/pdf': ['.pdf']
    }

    @classmethod
    def validate_file(
        cls,
        file_input: Union[UploadedFile, str, bytes, File],
        max_size_mb: int = 5,
        allowed_types: Optional[list] = None
    ) -> Tuple[bool, Optional[Union[UploadedFile, File]], Optional[str]]:
        """
        Comprehensive file validation method with multiple fallback strategies
        """
        try:
            # Set default allowed types if not provided
            if allowed_types is None:
                allowed_types = list(cls.ALLOWED_MIME_TYPES.keys())

            # Attempt magic-based detection first
            try:
                return cls._validate_with_magic(file_input, max_size_mb, allowed_types)
            except ImportError:
                # Fallback to extension-based detection
                return cls._validate_by_extension(file_input, max_size_mb, allowed_types)

        except Exception as e:
            logger.error(f"Unexpected file validation error: {str(e)}")
            return False, None, f"Validation error: {str(e)}"

    @classmethod
    def _validate_with_magic(
        cls,
        file_input: Union[UploadedFile, str, bytes, File],
        max_size_mb: int,
        allowed_types: list
    ) -> Tuple[bool, Optional[Union[UploadedFile, File]], Optional[str]]:
        """
        Validate file using python-magic library
        """
        import magic

        try:
            # Handle different input types
            if isinstance(file_input, str):
                # File path
                file_mime = magic.from_file(file_input, mime=True)
                file_size = os.path.getsize(file_input)
            elif isinstance(file_input, bytes):
                # Bytes input
                file_mime = magic.from_buffer(file_input, mime=True)
                file_size = len(file_input)
            elif hasattr(file_input, 'read'):
                # File-like object
                content = file_input.read(2048)
                file_input.seek(0)
                file_mime = magic.from_buffer(content, mime=True)
                file_size = file_input.size
            else:
                return False, None, "Unsupported input type"

            # Size validation
            max_size_bytes = max_size_mb * 1024 * 1024
            if file_size > max_size_bytes:
                return False, None, f"File too large. Max size: {max_size_mb}MB"

            # MIME type validation
            if file_mime not in allowed_types:
                return (
                    False,
                    None,
                    f"Invalid file type. Allowed: {', '.join(allowed_types)}"
                )

            return True, file_input, None

        except Exception as e:
            logger.error(f"Magic-based validation error: {str(e)}")
            return False, None, str(e)

    @classmethod
    def _validate_by_extension(
        cls,
        file_input: Union[UploadedFile, str, bytes, File],
        max_size_mb: int,
        allowed_types: list
    ) -> Tuple[bool, Optional[Union[UploadedFile, File]], Optional[str]]:
        """
        Fallback validation using file extension
        """
        try:
            # Determine file size and extension
            if isinstance(file_input, str):
                # File path
                file_size = os.path.getsize(file_input)
                file_ext = os.path.splitext(file_input)[1].lower()
            elif isinstance(file_input, bytes):
                # Bytes input
                file_size = len(file_input)
                file_ext = ''  # Cannot determine extension from bytes
            elif hasattr(file_input, 'name'):
                # File-like object
                file_size = file_input.size
                file_ext = os.path.splitext(file_input.name)[1].lower()
            else:
                return False, None, "Unsupported input type"

            # Size validation
            max_size_bytes = max_size_mb * 1024 * 1024
            if file_size > max_size_bytes:
                return False, None, f"File too large. Max size: {max_size_mb}MB"

            # Extension-based MIME type validation
            detected_mime = cls._get_mime_type_from_extension(file_ext)
            if detected_mime not in allowed_types:
                return (
                    False,
                    None,
                    f"Invalid file type. Allowed: {', '.join(allowed_types)}"
                )

            return True, file_input, None

        except Exception as e:
            logger.error(f"Extension-based validation error: {str(e)}")
            return False, None, str(e)

    @classmethod
    def _get_mime_type_from_extension(cls, file_ext: str) -> Optional[str]:
        """
        Get MIME type from file extension
        """
        for mime_type, extensions in cls.ALLOWED_MIME_TYPES.items():
            if file_ext.lower() in extensions:
                return mime_type
        return None

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent security issues
        """
        import re

        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)

        # Limit filename length
        return sanitized[:255]
