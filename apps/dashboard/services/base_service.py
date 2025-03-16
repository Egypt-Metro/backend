# apps/dashboard/services/base_service.py
import logging
from django.apps import apps

logger = logging.getLogger(__name__)


class BaseService:
    @classmethod
    def get_model(cls, app_label, model_name):
        """
        Safely retrieve a Django model dynamically with enhanced logging
        """
        try:
            model = apps.get_model(app_label, model_name)
            logger.info(f"Successfully loaded model {model_name} from {app_label}")
            return model
        except Exception as e:
            logger.error(f"Failed to load model {model_name} from {app_label}: {e}")
            raise ValueError(f"Could not import model {model_name} from {app_label}")

    @classmethod
    def log_service_error(cls, error, context=None):
        """
        Centralized error logging method
        """
        logger.error(f"Service Error: {str(error)}", extra={
            'context': context,
            'error_type': type(error).__name__
        })
