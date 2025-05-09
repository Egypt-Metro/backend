import json
from decimal import Decimal
from django.core.serializers.json import DjangoJSONEncoder


class DecimalEncoder(DjangoJSONEncoder):
    """Custom JSON encoder that can handle Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def json_serialize(data):
    """Utility function to serialize data to JSON, handling Decimal values"""
    return json.dumps(data, cls=DecimalEncoder)
