import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from ..models import DataType
from ..serializers.data_type_serializers import (
    DataTypeSerializer,
    DataTypeCreateUpdateSerializer,
    DataTypeListSerializer
)
from ..utils import api_response
from ..views.swagger import (
    data_type_list_swagger,
    data_type_create_swagger,
    data_type_update_swagger,
    data_type_delete_swagger,
)

logger = logging.getLogger(__name__)


# ============== Views ==============

@data_type_list_swagger()
@api_view(['GET'])
@permission_classes([IsAuthenticated])
# @cache_response(max_age=86400)  # Cache for 24 hours - static dropdown data
def data_type_list(request):
    """
    Get all data types.

    GET /data_types/

    Returns:
    - List of all data types with id, type, and validation_rules
    """
    try:
        data_types = DataType.objects.all().order_by('-id')
        serializer = DataTypeListSerializer(data_types, many=True)

        logger.info(f"User {request.user.id} retrieved data type list")

        return api_response(
            data={"data_types": serializer.data},
            message="Data types retrieved successfully"
        )
    except Exception as e:
        logger.exception("Error retrieving data types: %s", e)
        return api_response(
            message="Error retrieving data types",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@data_type_create_swagger()
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def data_type_create(request):
    """
    Create a new data type.

    POST /data_types/create/

    Request body:
    - name: Name of the data type (required)
    - validation_rules: JSON object with validation rules (optional)
    """
    serializer = DataTypeCreateUpdateSerializer(data=request.data)

    if not serializer.is_valid():
        return api_response(
            message="Validation failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        data_type = serializer.save()
        response_serializer = DataTypeSerializer(data_type)

        logger.info(f"User {request.user.id} created data type {data_type.id}")

        return api_response(
            data=response_serializer.data,
            message="Data type created successfully",
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        logger.exception("Error creating data type: %s", e)
        return api_response(
            message="Error creating data type",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@data_type_update_swagger()
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def data_type_update(request, pk):
    """
    Update an existing data type.

    PUT/PATCH /data_types/<pk>/update/

    Request body:
    - name: Name of the data type (required for PUT, optional for PATCH)
    - validation_rules: JSON object with validation rules (optional)
    """
    try:
        data_type = DataType.objects.filter(id=pk).first()

        if not data_type:
            return api_response(
                message="Data type not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # For PATCH, allow partial updates
        partial = request.method == 'PATCH'
        serializer = DataTypeCreateUpdateSerializer(
            data_type,
            data=request.data,
            partial=partial
        )

        if not serializer.is_valid():
            return api_response(
                message="Validation failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        data_type = serializer.save()
        response_serializer = DataTypeSerializer(data_type)

        logger.info(f"User {request.user.id} updated data type {pk}")

        return api_response(
            data=response_serializer.data,
            message="Data type updated successfully"
        )
    except Exception as e:
        logger.exception("Error updating data type: %s", e)
        return api_response(
            message="Error updating data type",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@data_type_delete_swagger()
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def data_type_delete(request, pk):
    """
    Delete a data type.

    DELETE /data_types/<pk>/delete/

    Note: Will fail if the data type is referenced by any FieldType.
    """
    try:
        data_type = DataType.objects.filter(id=pk).first()

        if not data_type:
            return api_response(
                message="Data type not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Check if data type is being used by any field types
        if data_type.field_types.exists():
            return api_response(
                message="Cannot delete data type as it is being used by field types",
                errors={"detail": "Data type is referenced by existing field types"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        data_type_id = data_type.id
        data_type_name = data_type.name
        data_type.delete()

        logger.info(f"User {request.user.id} deleted data type {data_type_id}")

        return api_response(
            data={"id": data_type_id, "name": data_type_name},
            message="Data type deleted successfully"
        )
    except Exception as e:
        logger.exception("Error deleting data type: %s", e)
        return api_response(
            message="Error deleting data type",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
