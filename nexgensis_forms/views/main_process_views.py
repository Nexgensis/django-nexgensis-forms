import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone

from ..models import MainProcess
from ..serializers.main_process_serializers import (
    MainProcessSerializer,
    MainProcessCreateUpdateSerializer,
    MainProcessListSerializer
)
from ..utils import api_response
from ..views.swagger import (
    main_process_list_swagger,
    main_process_create_swagger,
    main_process_detail_swagger,
    main_process_update_swagger,
    main_process_delete_swagger,
)

logger = logging.getLogger(__name__)


# ============== Views ==============

@main_process_list_swagger()
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def main_process_list(request):
    """
    Get all main processes.

    GET /main_processes/

    Returns:
    - List of all active main processes
    """
    try:
        main_processes = MainProcess.objects.filter(effective_end_date__isnull=True).order_by('-created_on')
        serializer = MainProcessListSerializer(main_processes, many=True)

        logger.info(f"User {request.user.id} retrieved main process list")

        return api_response(
            data=serializer.data,
            message="Main processes retrieved successfully"
        )
    except Exception as e:
        logger.exception("Error retrieving main processes: %s", e)
        return api_response(
            message="Error retrieving main processes",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@main_process_create_swagger()
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def main_process_create(request):
    """
    Create a new main process.

    POST /main_processes/create/

    Request body:
    - name: Name of the main process (required)
    """
    serializer = MainProcessCreateUpdateSerializer(data=request.data)

    if not serializer.is_valid():
        return api_response(
            message="Validation failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        main_process = serializer.save(created_by=request.user)
        response_serializer = MainProcessSerializer(main_process)

        logger.info(f"User {request.user.id} created main process {main_process.id}")

        return api_response(
            data=response_serializer.data,
            message="Main process created successfully",
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        logger.exception("Error creating main process: %s", e)
        return api_response(
            message="Error creating main process",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@main_process_detail_swagger()
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def main_process_detail(request, pk):
    """
    Get details of a specific main process.

    GET /main_processes/<pk>/

    Returns:
    - Main process details
    """
    try:
        main_process = MainProcess.objects.filter(id=pk, effective_end_date__isnull=True).first()

        if not main_process:
            return api_response(
                message="Main process not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = MainProcessSerializer(main_process)

        logger.info(f"User {request.user.id} retrieved main process {pk}")

        return api_response(
            data=serializer.data,
            message="Main process retrieved successfully"
        )
    except Exception as e:
        logger.exception("Error retrieving main process: %s", e)
        return api_response(
            message="Error retrieving main process",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@main_process_update_swagger()
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def main_process_update(request, pk):
    """
    Update an existing main process.

    PUT/PATCH /main_processes/<pk>/update/

    Request body:
    - name: Name of the main process (required for PUT, optional for PATCH)
    """
    try:
        main_process = MainProcess.objects.filter(id=pk, effective_end_date__isnull=True).first()

        if not main_process:
            return api_response(
                message="Main process not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # For PATCH, allow partial updates
        partial = request.method == 'PATCH'
        serializer = MainProcessCreateUpdateSerializer(
            main_process,
            data=request.data,
            partial=partial
        )

        if not serializer.is_valid():
            return api_response(
                message="Validation failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        main_process = serializer.save()
        response_serializer = MainProcessSerializer(main_process)

        logger.info(f"User {request.user.id} updated main process {pk}")

        return api_response(
            data=response_serializer.data,
            message="Main process updated successfully"
        )
    except Exception as e:
        logger.exception("Error updating main process: %s", e)
        return api_response(
            message="Error updating main process",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@main_process_delete_swagger()
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def main_process_delete(request, pk):
    """
    Delete a main process (soft delete by setting effective_end_date).

    DELETE /main_processes/<pk>/delete/
    """
    try:
        main_process = MainProcess.objects.filter(id=pk, effective_end_date__isnull=True).first()

        if not main_process:
            return api_response(
                message="Main process not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        main_process_id = main_process.id
        main_process_name = main_process.name

        # Soft delete by setting effective_end_date
        main_process.effective_end_date = timezone.now()
        main_process.save()

        logger.info(f"User {request.user.id} deleted main process {main_process_id}")

        return api_response(
            data={"id": main_process_id, "name": main_process_name},
            message="Main process deleted successfully"
        )
    except Exception as e:
        logger.exception("Error deleting main process: %s", e)
        return api_response(
            message="Error deleting main process",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
