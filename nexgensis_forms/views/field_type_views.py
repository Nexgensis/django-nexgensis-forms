import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from ..models import FieldType
from ..serializers.field_type_serializers import (
    FieldTypeListSerializer, FieldTypeSerializer, FieldTypeCreateUpdateSerializer
)
from ..utils import api_response
from djangoapp.utilities.custom_utils.cache_decorators import cache_response
from ..views.swagger import (
    field_type_list_swagger,
    field_type_create_swagger,
    field_type_update_swagger,
    field_type_delete_swagger,
)

logger = logging.getLogger(__name__)


# ============== FieldType Views ==============

@field_type_list_swagger()
@api_view(['GET'])
@permission_classes([IsAuthenticated])
# @cache_response(max_age=86400)  # Cache for 24 hours - static dropdown data
def field_type_list(request):
    """
    Get all field types.

    GET /field_types/
    """
    try:
        field_types = FieldType.objects.filter(is_deleted=False)
        serializer = FieldTypeListSerializer(field_types, many=True)

        logger.info(f"User {request.user.id} retrieved field type list")

        return api_response(
            data={"field_types": serializer.data},
            message="Field types retrieved successfully"
        )
    except Exception as e:
        logger.exception("Error retrieving field types: %s", e)
        return api_response(
            message="Error retrieving field types",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@field_type_create_swagger()
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def field_type_create(request):
    """
    Create a new field type or update existing one.

    POST /field_types/create/

    Request body:
    - field_type_id: ID for updating (optional)
    - label: Name of the field type (required)
    - type_id: ID of the data type (required)
    - validation_rules: JSON object (optional)
    - dynamic: Boolean (optional)
    - end_point: API endpoint for dynamic data (optional)
    """
    serializer = FieldTypeCreateUpdateSerializer(data=request.data)

    if not serializer.is_valid():
        return api_response(
            message="Validation failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        field_type_id = serializer.validated_data.get('field_type_id')

        if field_type_id:
            # Update existing
            field_type = FieldType.objects.filter(id=field_type_id, is_deleted=False).first()
            if not field_type:
                return api_response(
                    message="Field type not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            field_type = serializer.update(field_type, serializer.validated_data)
            message = "Field type updated successfully"
            status_code = status.HTTP_200_OK
        else:
            # Create new
            field_type = serializer.create(serializer.validated_data)
            message = "Field type created successfully"
            status_code = status.HTTP_201_CREATED

        response_serializer = FieldTypeSerializer(field_type)
        logger.info(f"User {request.user.id} {'updated' if field_type_id else 'created'} field type {field_type.id}")

        return api_response(
            data=response_serializer.data,
            message=message,
            status_code=status_code
        )
    except Exception as e:
        logger.exception("Error creating/updating field type: %s", e)
        return api_response(
            message="Error creating/updating field type",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    

@field_type_update_swagger()
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def field_type_update(request, pk):
    """
    Update an existing field type.

    PUT/PATCH /update_field_types/<pk>/
    """
    try:
        field_type = FieldType.objects.filter(id=pk, is_deleted=False).first()

        if not field_type:
            return api_response(
                message="Field type not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Add field_type_id to request data for validation
        data = request.data.copy()
        data['field_type_id'] = pk

        serializer = FieldTypeCreateUpdateSerializer(data=data)

        if not serializer.is_valid():
            return api_response(
                message="Validation failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        field_type = serializer.update(field_type, serializer.validated_data)
        response_serializer = FieldTypeSerializer(field_type)

        logger.info(f"User {request.user.id} updated field type {pk}")

        return api_response(
            data=response_serializer.data,
            message="Field type updated successfully"
        )
    except Exception as e:
        logger.exception("Error updating field type: %s", e)
        return api_response(
            message="Error updating field type",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@field_type_delete_swagger()
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def field_type_delete(request, pk):
    """
    Delete a field type (soft delete).

    DELETE /delete_field_types/<pk>/
    """
    try:
        field_type = FieldType.objects.filter(id=pk, is_deleted=False).first()

        if not field_type:
            return api_response(
                message="Field type not found or already deleted",
                status_code=status.HTTP_404_NOT_FOUND
            )

        field_type_id = field_type.id
        field_type_name = field_type.name
        field_type.delete()

        logger.info(f"User {request.user.id} deleted field type {field_type_id}")

        return api_response(
            data={"id": field_type_id, "name": field_type_name},
            message="Field type deleted successfully"
        )
    except Exception as e:
        logger.exception("Error deleting field type: %s", e)
        return api_response(
            message="Error deleting field type",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
