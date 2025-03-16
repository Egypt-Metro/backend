# apps/dashboard/utils/model_loader.py
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)


def load_model(app_label: str, model_name: str):
    """
    Dynamically load a Django model with error handling

    Args:
        app_label (str): The app label
        model_name (str): The model name

    Returns:
        Django model class

    Raises:
        ValueError: If model cannot be loaded
    """
    try:
        return apps.get_model(app_label, model_name)
    except (ImportError, ImproperlyConfigured) as e:
        logger.error(f"Failed to load model {model_name} from {app_label}: {e}")
        raise ValueError(f"Could not load model {model_name} from {app_label}")
