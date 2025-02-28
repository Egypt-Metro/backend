# apps/users/utils/response_helpers.py
from rest_framework import status
from rest_framework.response import Response


class ApiResponse:
    """Helper class for consistent API responses"""

    @staticmethod
    def success(data=None, message=None, status_code=status.HTTP_200_OK):
        response_data = {
            'success': True,
            'data': data
        }
        if message:
            response_data['message'] = message
        return Response(response_data, status=status_code)

    @staticmethod
    def error(message, status_code=status.HTTP_400_BAD_REQUEST):
        return Response({
            'success': False,
            'error': message
        }, status=status_code)

    @staticmethod
    def validation_error(errors):
        return Response({
            'success': False,
            'errors': errors
        }, status=status.HTTP_400_BAD_REQUEST)
