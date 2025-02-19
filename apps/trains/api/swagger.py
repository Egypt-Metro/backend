# apps/trains/api/swagger.py

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from apps.trains.api.serializers import TrainSerializer

train_list_docs = extend_schema(
    summary="List all trains",
    description="Get a list of all trains with optional filtering",
    parameters=[
        OpenApiParameter(
            name="line_id",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filter trains by line ID",
        ),
        OpenApiParameter(
            name="status",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filter trains by status",
        ),
    ],
    responses={200: TrainSerializer(many=True)},
)
