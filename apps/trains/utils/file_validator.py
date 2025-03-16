# apps/trains/utils/file_validator.py

import os
import magic  # For MIME type detection
from django.core.files import File


class FileValidator:
    """
    Comprehensive file validation utility
    """

    @staticmethod
    def validate_file(file_input):
        """
        Validate file input from various sources

        Args:
            file_input: Can be request.FILES, file path, or file-like object

        Returns:
            tuple: (is_valid, file_object, error_message)
        """
        try:
            # Case 1: Django request.FILES
            if hasattr(file_input, "file") or hasattr(file_input, "read"):
                return FileValidator._validate_file_object(file_input)

            # Case 2: File path as string
            elif isinstance(file_input, str):
                return FileValidator._validate_file_path(file_input)

            # Case 3: Unsupported input type
            else:
                return False, None, "Unsupported file input type"

        except Exception as e:
            return False, None, f"Unexpected error in file validation: {str(e)}"

    @staticmethod
    def _validate_file_object(file_obj):
        """
        Validate file object from request.FILES
        """
        try:
            # Check if file is empty
            if file_obj.size == 0:
                return False, None, "Empty file"

            # Detect MIME type
            file_mime = magic.from_buffer(file_obj.read(2048), mime=True)
            file_obj.seek(0)  # Reset file pointer

            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/jpg"]
            if file_mime not in allowed_types:
                return (
                    False,
                    None,
                    f"Invalid file type. Allowed: {', '.join(allowed_types)}",
                )

            # Size validation (e.g., max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB
            if file_obj.size > max_size:
                return (
                    False,
                    None,
                    f"File too large. Max size: {max_size / (1024 * 1024)}MB",
                )

            return True, file_obj, None

        except Exception as e:
            return False, None, f"File object validation error: {str(e)}"

    @staticmethod
    def _validate_file_path(file_path):
        """
        Validate file path
        """
        try:
            # Normalize and expand the path
            full_path = os.path.abspath(os.path.expanduser(file_path))

            # Check if path exists
            if not os.path.exists(full_path):
                return False, None, f"File does not exist: {full_path}"

            # Check if it's a file (not a directory)
            if not os.path.isfile(full_path):
                return False, None, f"Not a file: {full_path}"

            # Check file permissions
            if not os.access(full_path, os.R_OK):
                return False, None, f"No read permissions: {full_path}"

            # Check file size
            file_size = os.path.getsize(full_path)
            max_size = 5 * 1024 * 1024  # 5MB
            if file_size > max_size:
                return (
                    False,
                    None,
                    f"File too large. Max size: {max_size / (1024 * 1024)}MB",
                )

            # Detect MIME type
            file_mime = magic.from_file(full_path, mime=True)
            allowed_types = ["image/jpeg", "image/png", "image/jpg"]
            if file_mime not in allowed_types:
                return (
                    False,
                    None,
                    f"Invalid file type. Allowed: {', '.join(allowed_types)}",
                )

            # Open file and create Django File object
            file_obj = open(full_path, "rb")
            django_file = File(file_obj, name=os.path.basename(full_path))

            return True, django_file, None

        except PermissionError:
            return False, None, f"Permission denied: {file_path}"
        except Exception as e:
            return False, None, f"File path validation error: {str(e)}"
