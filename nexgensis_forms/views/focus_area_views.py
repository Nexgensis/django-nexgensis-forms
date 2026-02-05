import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone

from ..models import FocusArea
from ..serializers.focus_area_serializers import (
    FocusAreaSerializer,
    FocusAreaCreateUpdateSerializer,
    FocusAreaListSerializer
)
from ..utils import api_response
from ..views.swagger import (
    focus_area_list_swagger,
    focus_area_create_swagger,
    focus_area_detail_swagger,
    focus_area_update_swagger,
    focus_area_delete_swagger,
)

logger = logging.getLogger(__name__)


# ============== Views ==============

@focus_area_list_swagger()
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def focus_area_list(request):
    """
    Get all focus areas.

    GET /focus_areas/

    Returns:
    - List of all active focus areas
    """
    try:
        focus_areas = FocusArea.objects.filter(effective_end_date__isnull=True).order_by('-created_on')
        serializer = FocusAreaListSerializer(focus_areas, many=True)

        logger.info(f"User {request.user.id} retrieved focus area list")

        return api_response(
            data=serializer.data,
            message="Focus areas retrieved successfully"
        )
    except Exception as e:
        logger.exception("Error retrieving focus areas: %s", e)
        return api_response(
            message="Error retrieving focus areas",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@focus_area_create_swagger()
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def focus_area_create(request):
    """
    Create a new focus area.

    POST /focus_areas/create/

    Request body:
    - name: Name of the focus area (required)
    """
    serializer = FocusAreaCreateUpdateSerializer(data=request.data)

    if not serializer.is_valid():
        return api_response(
            message="Validation failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        focus_area = serializer.save(created_by=request.user)
        response_serializer = FocusAreaSerializer(focus_area)

        logger.info(f"User {request.user.id} created focus area {focus_area.id}")

        return api_response(
            data=response_serializer.data,
            message="Focus area created successfully",
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        logger.exception("Error creating focus area: %s", e)
        return api_response(
            message="Error creating focus area",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@focus_area_detail_swagger()
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def focus_area_detail(request, pk):
    """
    Get details of a specific focus area.

    GET /focus_areas/<pk>/

    Returns:
    - Focus area details
    """
    try:
        focus_area = FocusArea.objects.filter(id=pk, effective_end_date__isnull=True).first()

        if not focus_area:
            return api_response(
                message="Focus area not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = FocusAreaSerializer(focus_area)

        logger.info(f"User {request.user.id} retrieved focus area {pk}")

        return api_response(
            data=serializer.data,
            message="Focus area retrieved successfully"
        )
    except Exception as e:
        logger.exception("Error retrieving focus area: %s", e)
        return api_response(
            message="Error retrieving focus area",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@focus_area_update_swagger()
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def focus_area_update(request, pk):
    """
    Update an existing focus area.

    PUT/PATCH /focus_areas/<pk>/update/

    Request body:
    - name: Name of the focus area (required for PUT, optional for PATCH)
    """
    try:
        focus_area = FocusArea.objects.filter(id=pk, effective_end_date__isnull=True).first()

        if not focus_area:
            return api_response(
                message="Focus area not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # For PATCH, allow partial updates
        partial = request.method == 'PATCH'
        serializer = FocusAreaCreateUpdateSerializer(
            focus_area,
            data=request.data,
            partial=partial
        )

        if not serializer.is_valid():
            return api_response(
                message="Validation failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        focus_area = serializer.save()
        response_serializer = FocusAreaSerializer(focus_area)

        logger.info(f"User {request.user.id} updated focus area {pk}")

        return api_response(
            data=response_serializer.data,
            message="Focus area updated successfully"
        )
    except Exception as e:
        logger.exception("Error updating focus area: %s", e)
        return api_response(
            message="Error updating focus area",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@focus_area_delete_swagger()
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def focus_area_delete(request, pk):
    """
    Delete a focus area (soft delete by setting effective_end_date).

    DELETE /focus_areas/<pk>/delete/
    """
    try:
        focus_area = FocusArea.objects.filter(id=pk, effective_end_date__isnull=True).first()

        if not focus_area:
            return api_response(
                message="Focus area not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        focus_area_id = focus_area.id
        focus_area_name = focus_area.name

        # Soft delete by setting effective_end_date
        focus_area.effective_end_date = timezone.now()
        focus_area.save()

        logger.info(f"User {request.user.id} deleted focus area {focus_area_id}")

        return api_response(
            data={"id": focus_area_id, "name": focus_area_name},
            message="Focus area deleted successfully"
        )
    except Exception as e:
        logger.exception("Error deleting focus area: %s", e)
        return api_response(
            message="Error deleting focus area",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
