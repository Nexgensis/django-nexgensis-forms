import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone

from ..models import Criteria
from ..serializers.criteria_serializers import (
    CriteriaSerializer,
    CriteriaCreateUpdateSerializer,
    CriteriaListSerializer
)
from ..utils import api_response
from ..views.swagger import (
    criteria_list_swagger,
    criteria_create_swagger,
    criteria_detail_swagger,
    criteria_update_swagger,
    criteria_delete_swagger,
)

logger = logging.getLogger(__name__)


# ============== Views ==============

@criteria_list_swagger()
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def criteria_list(request):
    """
    Get all criteria.

    GET /criteria/

    Returns:
    - List of all active criteria
    """
    try:
        criteria = Criteria.objects.filter(effective_end_date__isnull=True).order_by('-created_on')
        serializer = CriteriaListSerializer(criteria, many=True)

        logger.info(f"User {request.user.id} retrieved criteria list")

        return api_response(
            data=serializer.data,
            message="Criteria retrieved successfully"
        )
    except Exception as e:
        logger.exception("Error retrieving criteria: %s", e)
        return api_response(
            message="Error retrieving criteria",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@criteria_create_swagger()
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def criteria_create(request):
    """
    Create a new criteria.

    POST /criteria/create/

    Request body:
    - name: Name of the criteria (required)
    """
    serializer = CriteriaCreateUpdateSerializer(data=request.data)

    if not serializer.is_valid():
        return api_response(
            message="Validation failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        criteria = serializer.save(created_by=request.user)
        response_serializer = CriteriaSerializer(criteria)

        logger.info(f"User {request.user.id} created criteria {criteria.id}")

        return api_response(
            data=response_serializer.data,
            message="Criteria created successfully",
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        logger.exception("Error creating criteria: %s", e)
        return api_response(
            message="Error creating criteria",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@criteria_detail_swagger()
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def criteria_detail(request, pk):
    """
    Get details of a specific criteria.

    GET /criteria/<pk>/

    Returns:
    - Criteria details
    """
    try:
        criteria = Criteria.objects.filter(id=pk, effective_end_date__isnull=True).first()

        if not criteria:
            return api_response(
                message="Criteria not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = CriteriaSerializer(criteria)

        logger.info(f"User {request.user.id} retrieved criteria {pk}")

        return api_response(
            data=serializer.data,
            message="Criteria retrieved successfully"
        )
    except Exception as e:
        logger.exception("Error retrieving criteria: %s", e)
        return api_response(
            message="Error retrieving criteria",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@criteria_update_swagger()
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def criteria_update(request, pk):
    """
    Update an existing criteria.

    PUT/PATCH /criteria/<pk>/update/

    Request body:
    - name: Name of the criteria (required for PUT, optional for PATCH)
    """
    try:
        criteria = Criteria.objects.filter(id=pk, effective_end_date__isnull=True).first()

        if not criteria:
            return api_response(
                message="Criteria not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # For PATCH, allow partial updates
        partial = request.method == 'PATCH'
        serializer = CriteriaCreateUpdateSerializer(
            criteria,
            data=request.data,
            partial=partial
        )

        if not serializer.is_valid():
            return api_response(
                message="Validation failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        criteria = serializer.save()
        response_serializer = CriteriaSerializer(criteria)

        logger.info(f"User {request.user.id} updated criteria {pk}")

        return api_response(
            data=response_serializer.data,
            message="Criteria updated successfully"
        )
    except Exception as e:
        logger.exception("Error updating criteria: %s", e)
        return api_response(
            message="Error updating criteria",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@criteria_delete_swagger()
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def criteria_delete(request, pk):
    """
    Delete a criteria (soft delete by setting effective_end_date).

    DELETE /criteria/<pk>/delete/
    """
    try:
        criteria = Criteria.objects.filter(id=pk, effective_end_date__isnull=True).first()

        if not criteria:
            return api_response(
                message="Criteria not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        criteria_id = criteria.id
        criteria_name = criteria.name

        # Soft delete by setting effective_end_date
        criteria.effective_end_date = timezone.now()
        criteria.save()

        logger.info(f"User {request.user.id} deleted criteria {criteria_id}")

        return api_response(
            data={"id": criteria_id, "name": criteria_name},
            message="Criteria deleted successfully"
        )
    except Exception as e:
        logger.exception("Error deleting criteria: %s", e)
        return api_response(
            message="Error deleting criteria",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
