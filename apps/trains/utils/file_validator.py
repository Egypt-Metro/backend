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
        Comprehensive file validation method

        Args:
            file_input: File to validate (various input types supported)
            max_size_mb: Maximum file size in megabytes
            allowed_types: Optional list of allowed MIME types

        Returns:
            Tuple of (is_valid, file_object, error_message)
        """
        try:
            # Set default allowed types if not provided
            if allowed_types is None:
                allowed_types = list(cls.ALLOWED_MIME_TYPES.keys())

            # Determine input type and validate accordingly
            if isinstance(file_input, str):
                return cls._validate_file_path(file_input, max_size_mb, allowed_types)
            elif isinstance(file_input, bytes):
                return cls._validate_file_bytes(file_input, max_size_mb, allowed_types)
            elif isinstance(file_input, (UploadedFile, File)):
                return cls._validate_file_object(file_input, max_size_mb, allowed_types)
            else:
                return False, None, "Unsupported file input type"

        except Exception as e:
            logger.error(f"Unexpected error in file validation: {str(e)}")
            return False, None, f"Validation error: {str(e)}"

    @classmethod
    def _validate_file_object(
        cls,
        file_obj: Union[UploadedFile, File],
        max_size_mb: int,
        allowed_types: list
    ) -> Tuple[bool, Optional[Union[UploadedFile, File]], Optional[str]]:
        """
        Validate file object from request.FILES or File
        """
        try:
            # Check if file is empty
            if file_obj.size == 0:
                return False, None, "Empty file"

            # Size validation
            max_size_bytes = max_size_mb * 1024 * 1024
            if file_obj.size > max_size_bytes:
                return (
                    False,
                    None,
                    f"File too large. Max size: {max_size_mb}MB"
                )

            # MIME type detection
            try:
                import magic
                file_mime = magic.from_buffer(file_obj.read(2048), mime=True)
                file_obj.seek(0)  # Reset file pointer
            except ImportError:
                # Fallback to extension-based detection
                file_ext = os.path.splitext(file_obj.name)[1].lower()
                file_mime = cls._get_mime_type_from_extension(file_ext)

            # Validate MIME type
            if file_mime not in allowed_types:
                return (
                    False,
                    None,
                    f"Invalid file type. Allowed: {', '.join(allowed_types)}"
                )

            return True, file_obj, None

        except Exception as e:
            logger.error(f"File object validation error: {str(e)}")
            return False, None, f"Validation error: {str(e)}"

    @classmethod
    def _validate_file_path(
        cls,
        file_path: str,
        max_size_mb: int,
        allowed_types: list
    ) -> Tuple[bool, Optional[File], Optional[str]]:
        """
        Validate file from file path
        """
        try:
            # Normalize path
            full_path = os.path.abspath(os.path.expanduser(file_path))

            # Check file existence and permissions
            if not os.path.exists(full_path):
                return False, None, f"File does not exist: {full_path}"

            if not os.path.isfile(full_path):
                return False, None, f"Not a file: {full_path}"

            if not os.access(full_path, os.R_OK):
                return False, None, f"No read permissions: {full_path}"

            # Size validation
            max_size_bytes = max_size_mb * 1024 * 1024
            file_size = os.path.getsize(full_path)
            if file_size > max_size_bytes:
                return (
                    False,
                    None,
                    f"File too large. Max size: {max_size_mb}MB"
                )

            # MIME type detection
            try:
                import magic
                file_mime = magic.from_file(full_path, mime=True)
            except ImportError:
                # Fallback to extension-based detection
                file_ext = os.path.splitext(full_path)[1].lower()
                file_mime = cls._get_mime_type_from_extension(file_ext)

            # Validate MIME type
            if file_mime not in allowed_types:
                return (
                    False,
                    None,
                    f"Invalid file type. Allowed: {', '.join(allowed_types)}"
                )

            # Create Django File object
            file_obj = open(full_path, 'rb')
            django_file = File(file_obj, name=os.path.basename(full_path))

            return True, django_file, None

        except PermissionError:
            return False, None, f"Permission denied: {file_path}"
        except Exception as e:
            logger.error(f"File path validation error: {str(e)}")
            return False, None, f"Validation error: {str(e)}"

    @classmethod
    def _validate_file_bytes(
        cls,
        file_bytes: bytes,
        max_size_mb: int,
        allowed_types: list
    ) -> Tuple[bool, Optional[File], Optional[str]]:
        """
        Validate file from bytes
        """
        try:
            # Size validation
            max_size_bytes = max_size_mb * 1024 * 1024
            if len(file_bytes) > max_size_bytes:
                return (
                    False,
                    None,
                    f"File too large. Max size: {max_size_mb}MB"
                )

            # MIME type detection
            try:
                import magic
                file_mime = magic.from_buffer(file_bytes, mime=True)
            except ImportError:
                # Fallback to None if magic is not available
                file_mime = None

            # Validate MIME type
            if file_mime not in allowed_types:
                return (
                    False,
                    None,
                    f"Invalid file type. Allowed: {', '.join(allowed_types)}"
                )

            # Create temporary file
            from tempfile import NamedTemporaryFile
            temp_file = NamedTemporaryFile(delete=False)
            temp_file.write(file_bytes)
            temp_file.close()

            # Create Django File object
            django_file = File(open(temp_file.name, 'rb'), name='uploaded_file')

            return True, django_file, None

        except Exception as e:
            logger.error(f"Bytes validation error: {str(e)}")
            return False, None, f"Validation error: {str(e)}"

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

        Args:
            filename (str): Original filename

        Returns:
            str: Sanitized filename
        """
        import re

        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)

        # Limit filename length
        return sanitized[:255]
