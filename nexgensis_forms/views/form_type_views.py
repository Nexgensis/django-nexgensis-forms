import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from ..models import FormType
from ..serializers.form_type_serializers import (
    FormTypeListSerializer,
    FormTypeSerializer,
    FormTypeCreateUpdateSerializer
)
from ..utils import api_response
from djangoapp.utilities.custom_utils.cache_decorators import cache_response
from ..views.swagger import (
    form_type_list_swagger,
    form_type_create_swagger,
    form_type_detail_swagger,
    form_type_update_swagger,
    form_type_delete_swagger,
)

logger = logging.getLogger(__name__)

DROPDOWN_PAGE_SIZE = 1000


# ============== FormType Views ==============

@form_type_list_swagger()
@api_view(['GET'])
@permission_classes([IsAuthenticated])
# @cache_response(max_age=43200)  # Cache for 12 hours - dropdown data
def form_type_list(request):
    """
    Get all form types with optional pagination.

    GET /form_types/

    Query Parameters:
    - search: Search by name
    - order_by: Field to order by (default: 'name')
    - page: Page number (optional - enables pagination)
    - page_size: Records per page (optional - enables pagination, default: 8)
    - source: Use 'dropdown' for dropdown source (page_size=1000)
    """
    try:
        # Get query parameters
        search = request.GET.get('search', '').strip()
        order_by = request.GET.get('order_by', 'name')
        source = request.GET.get('source')
        page_param = request.GET.get('page')
        page_size_param = request.GET.get('page_size')

        # Check if pagination is requested
        use_pagination = page_param is not None or page_size_param is not None or source == 'dropdown'

        # Build query
        query = Q(effective_end_date__isnull=True)
        if search:
            query &= Q(name__icontains=search)

        # Get queryset
        queryset = FormType.objects.filter(query).order_by(order_by)

        if use_pagination:
            # Apply pagination
            page = int(page_param) if page_param else 1
            if source == 'dropdown':
                page_size = DROPDOWN_PAGE_SIZE
            else:
                page_size = int(page_size_param) if page_size_param else 8

            paginator = Paginator(queryset, page_size)
            try:
                paginated_page = paginator.page(page)
            except PageNotAnInteger:
                paginated_page = paginator.page(1)
            except EmptyPage:
                paginated_page = paginator.page(paginator.num_pages) if paginator.num_pages > 0 else []

            # Serialize
            if paginated_page:
                serializer = FormTypeListSerializer(paginated_page.object_list, many=True)
                data = serializer.data
                pagination = {
                    "current_page": paginated_page.number,
                    "total_pages": paginator.num_pages,
                    "total_records": paginator.count,
                    "page_size": page_size,
                }
            else:
                data = []
                pagination = {
                    "current_page": 1,
                    "total_pages": 0,
                    "total_records": 0,
                    "page_size": page_size,
                }

            logger.info(f"User {request.user.id} retrieved form type list with pagination")

            return api_response(
                data=data,
                message="Form types retrieved successfully",
                pagination=pagination
            )
        else:
            # Return all results without pagination
            serializer = FormTypeListSerializer(queryset, many=True)

            logger.info(f"User {request.user.id} retrieved form type list")

            return api_response(
                data=serializer.data,
                message="Form types retrieved successfully"
            )
    except Exception as e:
        logger.exception("Error retrieving form types: %s", e)
        return api_response(
            message="Error retrieving form types",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@form_type_create_swagger()
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def form_type_create(request):
    """
    Create a new form type.

    POST /form_types/create/

    Request body:
    - name: Name of the form type (required, max 100 chars)
    - description: Description (optional)
    - parent_form_type_id: ID of parent form type (optional)
    """
    serializer = FormTypeCreateUpdateSerializer(data=request.data)

    if not serializer.is_valid():
        # Extract first error message for user-friendly response
        first_error = next(iter(serializer.errors.values()))[0]
        return api_response(
            message=str(first_error),
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        form_type = serializer.save()

        # Track creator
        form_type.created_by = request.user
        form_type.save(update_fields=['created_by'])

        response_serializer = FormTypeSerializer(form_type)

        logger.info(f"User {request.user.id} created form type {form_type.id}")

        return api_response(
            data=response_serializer.data,
            message=f"FormType '{form_type.name}' created successfully",
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        logger.exception("Error creating form type: %s", e)
        return api_response(
            message="Error creating form type",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@form_type_detail_swagger()
@api_view(['GET'])
@permission_classes([IsAuthenticated])
# @cache_response(max_age=86400)  # Cache for 24 hours - static record
def form_type_detail(request, pk):
    """
    Get a specific form type by ID.

    GET /form_types/<pk>/
    """
    try:
        form_type = FormType.objects.filter(unique_code=pk, effective_end_date__isnull=True).first()

        if not form_type:
            return api_response(
                message="FormType not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = FormTypeSerializer(form_type)

        logger.info(f"User {request.user.id} retrieved form type {pk}")

        return api_response(
            data=serializer.data,
            message="FormType retrieved successfully"
        )
    except Exception as e:
        logger.exception("Error retrieving form type: %s", e)
        return api_response(
            message="Error retrieving form type",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@form_type_update_swagger()
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def form_type_update(request, pk):
    """
    Update an existing form type with optimistic locking.

    PUT/PATCH /form_types/<pk>/update/

    Request body:
    - name: Name of the form type (required for PUT, optional for PATCH)
    - description: Description (optional)
    - parent_form_type_id: ID of parent form type (optional, set to null to remove parent)
    - version_id: UUID of the version being edited (required for optimistic locking)

    Note:
    - version_id is REQUIRED to prevent concurrent modification conflicts
    """
    try:
        # # REQUIRED: Optimistic locking - version_id must be provided
        # version_id = request.data.get('version_id')

        # if not version_id:
        #     return api_response(
        #         message="version_id is required for optimistic locking",
        #         errors={"version_id": "This field is required to prevent concurrent modification conflicts"},
        #         status_code=status.HTTP_400_BAD_REQUEST
        #     )

        # # Verify version_id matches current active version (optimistic locking)
        # form_type = FormType.objects.filter(
        #     id=version_id,
        #     effective_end_date__isnull=True
        # ).first()

        # if not form_type:
        #     return api_response(
        #         message="Record has been modified or deleted by another user. Please refresh and try again.",
        #         errors={"conflict": "Please refresh and try again"},
        #         status_code=status.HTTP_409_CONFLICT
        #     )

        # # Verify it matches the pk
        # if str(form_type.id) != str(pk):
        #     return api_response(
        #         message="Version mismatch. Please refresh and try again.",
        #         errors={"conflict": "Version ID doesn't match form type ID"},
        #         status_code=status.HTTP_409_CONFLICT
        #     )

        # Get form type by unique_code
        form_type = FormType.objects.filter(unique_code=pk, effective_end_date__isnull=True).first()

        if not form_type:
            return api_response(
                message="FormType not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # For PATCH, allow partial updates
        partial = request.method == 'PATCH'
        serializer = FormTypeCreateUpdateSerializer(
            form_type,
            data=request.data,
            partial=partial
        )

        if not serializer.is_valid():
            return api_response(
                message="Validation failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        form_type = serializer.save()
        response_serializer = FormTypeSerializer(form_type)

        logger.info(f"User {request.user.id} updated form type {pk}")

        return api_response(
            data=response_serializer.data,
            message="FormType updated successfully"
        )
    except Exception as e:
        logger.exception("Error updating form type: %s", e)
        return api_response(
            message="Error updating form type",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@form_type_delete_swagger()
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def form_type_delete(request, pk):
    """
    Delete a form type (soft delete).

    DELETE /form_types/<pk>/delete/

    Note: Will fail if the form type has associated forms.
    """
    try:
        form_type = FormType.objects.filter(unique_code=pk, effective_end_date__isnull=True).first()

        if not form_type:
            return api_response(
                message="FormType not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Check if form type is being used by any forms
        if form_type.form_set.filter(effective_end_date__isnull=True).exists():
            return api_response(
                message="Cannot delete FormType as it is being used by forms",
                errors={"detail": "FormType is referenced by existing forms"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Check if form type has sub-types
        if form_type.sub_forms.filter(effective_end_date__isnull=True).exists():
            return api_response(
                message="Cannot delete FormType as it has sub-types",
                errors={"detail": "FormType has child form types"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        form_type_id = form_type.id
        form_type_name = form_type.name
        # Use TimestampedModel2's built-in soft delete (sets effective_end_date)
        form_type.delete()

        logger.info(f"User {request.user.id} deleted form type {form_type_id}")

        return api_response(
            data={"id": form_type_id, "name": form_type_name},
            message=f"FormType with ID {form_type_id} deleted successfully"
        )
    except Exception as e:
        logger.exception("Error deleting form type: %s", e)
        return api_response(
            message="Error deleting form type",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
