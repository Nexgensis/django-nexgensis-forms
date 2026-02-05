import logging
import math
from ..utils import validate_id
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q, Max

from ..models import (
    FieldType, Form, FormType, FormDraft, FormSections, FormFields,
    MainProcess, Criteria
)
try:
    from configapp.models import Location
except ImportError:
    Location = None  # Optional - configure via NEXGENSIS_FORMS settings
from ..serializers.form_design_serializers import (
    FormSerializer, FormCreateSerializer, DynamicFormResponseSerializer
)
from ..utils import api_response
from djangoapp.utilities.custom_utils.cache_decorators import cache_response
from ..utils import format_user_timezone
try:
    from ticketworkflowapp.models import WorkflowChecklist
except ImportError:
    WorkflowChecklist = None  # Optional - requires workflow integration
from ..views.swagger import (
    get_dynamic_forms_swagger,
    form_create_swagger,
    form_detail_swagger,
    forms_by_type_swagger,
    create_form_fields_swagger,
    get_form_fields_swagger,
    form_with_sections_list_swagger,
)

logger = logging.getLogger(__name__)


# ============== Form Views ==============

@get_dynamic_forms_swagger()
@api_view(['GET'])
@permission_classes([IsAuthenticated])
# @cache_response(max_age=600)  # Cache for 10 minutes - form listing
def get_dynamic_forms(request):
    """
    Get dynamic forms with pagination and filters.

    GET /get_dynamic_forms/

    Query Parameters:
    - page_number: Page number (default: 1)
    - search: Search by title
    - is_completed: Filter by completion status (default: true)
    - form_type_id: Filter by form type (unique_code or UUID)
    - form_type_name: Filter by form type name (case-insensitive)
    - workflow_type_id: Filter by workflow type
    - workflow_name_id: Filter by workflow ID
    - main_process: Filter by main process UUID
    - criteria: Filter by criteria UUID
    - location: Filter by location UUID
    """
    try:
        page_number = int(request.GET.get("page_number", 1))
        max_rows = 9
        start = (page_number - 1) * max_rows
        end = page_number * max_rows

        query = Q(effective_end_date__isnull=True)

        # Search filter
        search_title = request.GET.get("search", "").strip()
        if search_title:
            query &= Q(title__icontains=search_title)

        # Completion filter (default to True - only show completed forms)
        is_completed_param = request.GET.get("is_completed", "true")
        if is_completed_param.lower() == "true":
            query &= Q(is_completed=True)
            is_completed = True
        elif is_completed_param.lower() == "false":
            query &= Q(is_completed=False)
            is_completed = False
        else:
            is_completed = None  # No filter applied if invalid value

        # Form type filter - support unique_code, UUID, or name
        form_type_id = request.GET.get("form_type_id")
        form_type_name = request.GET.get("form_type_name")

        if form_type_id or form_type_name:
            form_type_obj = None

            if form_type_id:
                # Try lookup by unique_code first
                form_type_obj = FormType.objects.filter(
                    unique_code=form_type_id,
                    effective_end_date__isnull=True
                ).first()

                # Fallback to UUID
                if not form_type_obj:
                    form_type_obj = FormType.objects.filter(
                        id=form_type_id,
                        effective_end_date__isnull=True
                    ).first()

            elif form_type_name:
                # Lookup by name (case-insensitive)
                form_type_obj = FormType.objects.filter(
                    name__iexact=form_type_name,
                    effective_end_date__isnull=True
                ).first()

            if form_type_obj:
                query &= Q(form_type_id=form_type_obj.id)
            else:
                # If form type not found, return empty results
                return api_response(
                    data={
                        "forms": [],
                        "obj_count": 0,
                        "max_pages": 1,
                        "max_rows": max_rows
                    },
                    message="FormType not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

        # Workflow filters
        workflow_type_id = request.GET.get("workflow_type_id")
        if workflow_type_id:
            workflow_checklists = WorkflowChecklist.objects.filter(
                workflow_stage__workflow__type_id=workflow_type_id
            ).values_list("checklist_id", flat=True)
            query &= Q(id__in=workflow_checklists)

        workflow_name_id = request.GET.get("workflow_name_id")
        if workflow_name_id:
            workflow_checklists = WorkflowChecklist.objects.filter(
                workflow_stage__workflow_id=workflow_name_id
            ).values_list("checklist_id", flat=True)
            query &= Q(id__in=workflow_checklists)

        # Filter by main_process
        main_process_id = request.GET.get("main_process")
        if main_process_id:
            main_process_obj = MainProcess.objects.filter(
                id=main_process_id,
                effective_end_date__isnull=True
            ).first()
            if main_process_obj:
                query &= Q(main_process_id=main_process_obj.id)
            else:
                return api_response(
                    data={
                        "forms": [],
                        "obj_count": 0,
                        "max_pages": 1,
                        "max_rows": max_rows
                    },
                    message="Main process not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

        # Filter by criteria
        criteria_id = request.GET.get("criteria")
        if criteria_id:
            criteria_obj = Criteria.objects.filter(
                id=criteria_id,
                effective_end_date__isnull=True
            ).first()
            if criteria_obj:
                query &= Q(criteria_id=criteria_obj.id)
            else:
                return api_response(
                    data={
                        "forms": [],
                        "obj_count": 0,
                        "max_pages": 1,
                        "max_rows": max_rows
                    },
                    message="Criteria not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

        # Filter by location
        location_id = request.GET.get("location")
        if location_id:
            location_obj = Location.objects.filter(
                id=location_id,
                effective_end_date__isnull=True
            ).first()
            if location_obj:
                query &= Q(location_id=location_obj.id)
            else:
                return api_response(
                    data={
                        "forms": [],
                        "obj_count": 0,
                        "max_pages": 1,
                        "max_rows": max_rows
                    },
                    message="Location not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

        # Get all forms matching the query
        all_forms = Form.objects.filter(query)

        # Group by root and find latest version IDs
        latest_form_ids = {}
        for form in all_forms.order_by('version'):
            root_id = form.root_form_id if form.root_form_id else form.id
            latest_form_ids[root_id] = form.id

        # Filter to get only latest versions
        latest_forms = Form.objects.filter(
            id__in=latest_form_ids.values()
        ).select_related(
            'form_type', 'main_process', 'criteria', 'location'
        ).order_by("-id")

        forms_count = latest_forms.count()
        max_page_number = math.ceil(forms_count / max_rows) if forms_count > 0 else 1
        forms = latest_forms[start:end]

        # Use serializer for consistent response format
        # Don't include all_versions when is_completed=false
        include_all_versions = is_completed is not False
        serializer = DynamicFormResponseSerializer(
            forms, many=True, context={'include_all_versions': include_all_versions}
        )

        logger.info(f"User {request.user.id} retrieved form list")

        return api_response(
            data={
                "forms": serializer.data,
                "obj_count": forms_count,
                "max_pages": max_page_number,
                "max_rows": max_rows
            },
            message="Forms retrieved successfully"
        )
    except Exception as e:
        logger.exception("Error retrieving forms: %s", e)
        return api_response(
            message="Error retrieving forms",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@form_create_swagger()
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def form_create(request):
    """
    Create a new dynamic form.

    POST /forms/create/

    Request body:
    - title: Title of the form (required)
    - type_id: ID of the form type (required)
    - desc: Description (optional)
    - system_config: System configuration (optional)
    - user_config: User configuration (optional)
    - main_process: UUID of the main process (optional)
    - criteria: UUID of the criteria (optional)
    - location: unique_code or UUID of the location (optional)
    """
    serializer = FormCreateSerializer(data=request.data)

    if not serializer.is_valid():
        # Extract first error message for user-friendly message
        first_error = next(iter(serializer.errors.values()))[0] if serializer.errors else "Validation failed"
        return api_response(
            message=str(first_error),
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        form = serializer.save()

        # Set created_by for audit trail
        form.created_by = request.user
        form.save(update_fields=['created_by'])

        # Create FormDraft for the new form
        FormDraft.objects.create(form=form, draft_data={})

        response_serializer = FormSerializer(form)

        logger.info(f"User {request.user.id} created form {form.id}")

        return api_response(
            data={
                **response_serializer.data,
                "form_id": form.id
            },
            message="Dynamic form created successfully",
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        logger.exception("Error creating form: %s", e)
        return api_response(
            message="Error creating form",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@form_detail_swagger()
@api_view(['GET'])
@permission_classes([IsAuthenticated])
# @cache_response(max_age=900)  # Cache for 15 minutes - form detail
def form_detail(request, pk):
    """
    Get a specific form by ID.

    GET /forms/<pk>/
    """
    try:
        form = Form.objects.filter(id=pk, effective_end_date__isnull=True).first()

        if not form:
            return api_response(
                message="Form not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = FormSerializer(form)

        logger.info(f"User {request.user.id} retrieved form {pk}")

        return api_response(
            data=serializer.data,
            message="Form retrieved successfully"
        )
    except Exception as e:
        logger.exception("Error retrieving form: %s", e)
        return api_response(
            message="Error retrieving form",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@forms_by_type_swagger()
@api_view(['GET'])
@permission_classes([IsAuthenticated])
# @cache_response(max_age=600)  # Cache for 10 minutes - filtered form dropdown
def forms_by_type(request):
    """
    Get forms filtered by type.

    GET /forms/by_type/

    Query Parameters:
    - type: Form type ID or name
    - search: Search by title
    """
    try:
        form_type_param = request.GET.get("type")
        query = Q(effective_end_date__isnull=True, is_completed=True)

        if form_type_param:
            # Check if it's a unique_code (e.g., "FTYPE-XXXX")
            if form_type_param.startswith("FTYPE-"):
                query &= Q(form_type__unique_code=form_type_param)
            elif validate_id(form_type_param):
                # Valid UUID
                query &= Q(form_type_id=form_type_param)
            else:
                # Fallback to name lookup
                form_type = FormType.objects.filter(name__iexact=form_type_param).first()
                if not form_type:
                    return api_response(
                        message=f"No FormType found for '{form_type_param}'",
                        status_code=status.HTTP_404_NOT_FOUND
                    )
                query &= Q(form_type=form_type)

        search_title = request.GET.get("search", "").strip()
        if search_title:
            query &= Q(title__icontains=search_title)

        forms = Form.objects.filter(query).order_by("-id")

        response = []
        for form in forms:
            response.append({
                "id": form.id,
                "name": form.title,
                "title": form.title,
                "type": form.form_type.name if form.form_type else None,
                "description": form.description,
                "is_completed": form.is_completed,
                "version": form.version,
                "parent_form": form.parent_form_id,
                "root_form": form.root_form_id,
            })

        logger.info(f"User {request.user.id} retrieved forms by type")

        return api_response(
            data=response,
            message="Forms retrieved successfully"
        )
    except Exception as e:
        logger.exception("Error retrieving forms by type: %s", e)
        return api_response(
            message="Error retrieving forms",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============== Form Fields Views ==============

@create_form_fields_swagger()
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def create_form_fields(request, form_id):
    """
    Create fields for a form with optimistic locking.

    POST /create_form_fields/<form_id>/

    Request body:
    - sections: List of sections with fields (required)
    - form_details: Form metadata (title, description, form_type) (optional)
    - version_id: UUID of the version being edited (required for optimistic locking)
    - system_config: System configuration (optional)
    - user_config: User configuration (optional)

    Note:
    - form_id can be either unique_code (FORM-XXXXXXXX) or UUID
    - form_details.form_type can be either FormType unique_code or UUID
    - version_id is REQUIRED to prevent concurrent modification conflicts
    """
    try:
        if not form_id:
            return api_response(
                message="Form ID is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # # REQUIRED: Optimistic locking - version_id must be provided
        # version_id = request.data.get('version_id')

        # if not version_id:
        #     return api_response(
        #         message="version_id is required for optimistic locking",
        #         errors={"version_id": "This field is required to prevent concurrent modification conflicts"},
        #         status_code=status.HTTP_400_BAD_REQUEST
        #     )

        # # Verify version_id matches current active version (optimistic locking)
        # form = Form.objects.filter(
        #     id=version_id,
        #     effective_end_date__isnull=True
        # ).first()

        # if not form:
        #     return api_response(
        #         message="Record has been modified or deleted by another user. Please refresh and try again.",
        #         errors={"conflict": "Please refresh and try again"},
        #         status_code=status.HTTP_409_CONFLICT
        #     )

        # # Verify it matches the form_id (can be unique_code or UUID)
        # if str(form.id) != str(form_id) and form.unique_code != form_id:
        #     return api_response(
        #         message="Version mismatch. Please refresh and try again.",
        #         errors={"conflict": "Version ID doesn't match form ID"},
        #         status_code=status.HTTP_409_CONFLICT
        #     )

        # Get form by unique_code or UUID
        form = Form.objects.filter(
            unique_code=form_id,
            effective_end_date__isnull=True
        ).first()

        # Fallback to UUID lookup
        if not form:
            form = Form.objects.filter(
                id=form_id,
                effective_end_date__isnull=True
            ).first()

        if not form:
            return api_response(
                message="Form not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        data = request.data
        if not data:
            return api_response(
                message="Draft data is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        sections = data.get("sections", [])

        # Extract form_details if provided
        form_details = data.get('form_details', {})

        # Process form_type lookup if provided in form_details
        form_type_obj = None
        if form_details.get('form_type'):
            form_type_identifier = form_details['form_type']

            # Try lookup by unique_code first
            form_type_obj = FormType.objects.filter(
                unique_code=form_type_identifier,
                effective_end_date__isnull=True
            ).first()

            # Fallback to UUID
            if not form_type_obj:
                form_type_obj = FormType.objects.filter(
                    id=form_type_identifier,
                    effective_end_date__isnull=True
                ).first()

            if not form_type_obj:
                return api_response(
                    message="FormType not found",
                    errors={"form_type": "Invalid FormType identifier"},
                    status_code=status.HTTP_404_NOT_FOUND
                )

        # Helper function to create fields recursively
        def create_fields(fields, section, parent_field=None):
            for idx, field in enumerate(fields):
                field_type_id = field.get("type_id")
                field_type_obj = FieldType.objects.get(id=field_type_id)

                # Extract dependency separately
                field_dependency = field.get("dependency", {})

                additional_info = {
                    key: value for key, value in field.items()
                    if key not in {'label', 'name', 'type', 'type_id', 'required', 'fields','dependency'}
                }

                form_field = FormFields.objects.create(
                    label=field.get("label"),
                    name=field.get("name"),
                    field_type=field_type_obj,
                    section=section,
                    required=field.get("required", False),
                    order=idx,
                    additional_info=additional_info,
                    parent_field=parent_field,
                    dependency=field_dependency
                )

                # Recursive children
                if field.get("fields") and isinstance(field["fields"], list):
                    create_fields(field["fields"], section, parent_field=form_field)

        # Check if form is attached to a workflow
        is_linked_to_workflow = WorkflowChecklist.objects.filter(checklist_id=form.id).exists()

        if is_linked_to_workflow:
            # Create new version
            root_form = form.root_form if form.root_form else form

            max_version = (
                Form.objects.filter(root_form=root_form, effective_end_date__isnull=True)
                .aggregate(Max("version"))["version__max"] or 1
            )
            next_version = max_version + 1

            new_form = Form.objects.create(
                title=form_details.get('title', root_form.title),
                form_type=form_type_obj if form_type_obj else form.form_type,
                description=form_details.get('description', form.description),
                parent_form=form,
                root_form=root_form,
                version=next_version,
                system_config=data.get("system_config", {}),
                user_config=data.get("user_config", {}),
                is_completed=False,
                created_by=request.user,  # Track creator
                previous_version_id=form.id  # Link to previous version
            )

            form_draft = FormDraft.objects.create(form=new_form, draft_data=data)

            # Save sections and fields
            for section_data in sections:
                section_name = section_data.get("section_name")
                if not section_name:
                    transaction.set_rollback(True)
                    return api_response(
                        message="Section name is required",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                section_dependency = section_data.get("dependency", {})
                section, _ = FormSections.objects.get_or_create(form=new_form, name=section_name)
                section.dependency = section_dependency
                section.save()
                create_fields(section_data.get("fields", []), section)

            new_form.is_completed = True
            new_form.save()

            logger.info(f"User {request.user.id} created new form version {new_form.id}")

            return api_response(
                data={
                    "form_draft_id": form_draft.id,
                    "form_id": new_form.id,
                    "version": new_form.version,
                    "version_id": new_form.id,  # Return version_id
                    "unique_code": new_form.unique_code  # Return unique_code
                },
                message="This form is linked to a workflow, creating a new version and saving fields.",
                status_code=status.HTTP_201_CREATED
            )

        else:
            # Simple in-place update (no SCD Type 2 versioning)
            # Update form details
            if form_details.get('title'):
                form.title = form_details['title']
            if form_details.get('description') is not None:
                form.description = form_details['description']
            if form_type_obj:
                form.form_type = form_type_obj
            if data.get("system_config"):
                form.system_config = data["system_config"]
            if data.get("user_config"):
                form.user_config = data["user_config"]

            # Delete existing sections and fields
            FormSections.objects.filter(form=form).delete()

            # Create new sections and fields
            for section_data in sections:
                section_name = section_data.get("section_name")
                if not section_name:
                    transaction.set_rollback(True)
                    return api_response(
                        message="Section name is required",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

                section_dependency = section_data.get("dependency", {})
                section = FormSections.objects.create(form=form, name=section_name, dependency=section_dependency)
                create_fields(section_data.get("fields", []), section)

            form.is_completed = True
            form.save()

            # Update or create form draft
            form_draft, _ = FormDraft.objects.update_or_create(
                form=form,
                defaults={'draft_data': data}
            )

            logger.info(f"User {request.user.id} updated form fields for form {form_id}")

            return api_response(
                data={
                    "form_draft_id": form_draft.id,
                    "form_id": form.id,
                    "version": form.version,
                    "version_id": form.id,
                    "unique_code": form.unique_code
                },
                message="Form fields updated successfully"
            )

    except FieldType.DoesNotExist:
        transaction.set_rollback(True)
        return api_response(
            message="Field type not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        transaction.set_rollback(True)
        logger.exception("Error creating form fields: %s", e)
        return api_response(
            message="Error creating form fields",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@get_form_fields_swagger()
@api_view(['GET'])
@permission_classes([IsAuthenticated])
# @cache_response(max_age=900)  # Cache for 15 minutes - form fields
def get_form_fields(request, form_id):
    """
    Get all fields for a form.

    GET /get_form_fields/<form_id>/

    Note:
    - form_id can be either unique_code (FORM-XXXXXXXX) or UUID
    """
    try:
        # Get form by unique_code or UUID
        form = Form.objects.filter(
            unique_code=form_id,
            effective_end_date__isnull=True
        ).first()

        # Fallback to UUID lookup if not found by unique_code
        if not form:
            form = Form.objects.filter(id=form_id).first()

        if not form:
            return api_response(
                message="Form not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        sections = FormSections.objects.filter(form=form)

        workflow_name = None
        workflow_checklist = WorkflowChecklist.objects.filter(checklist=form).first()
        if workflow_checklist:
            workflow_name = workflow_checklist.workflow_stage.workflow.name

        def serialize_field(field):
            data = {
                "field_id": field.id,
                "label": field.label,
                "name": field.name,
                "type_id": field.field_type.data_type.id,
                "type": field.field_type.data_type.name,
                "required": field.required,
                "dependency": field.dependency or {},
                "dynamic": field.field_type.dynamic if field.field_type else False,
                "end_point": field.field_type.endpoint,
                **{k: v for k, v in (field.additional_info or {}).items() if k != "end_point"}
            }

            sub_fields = field.sub_fields.all()
            if sub_fields.exists():
                data["fields"] = [serialize_field(f) for f in sub_fields]

            return data

        response_data = {
            "form_id": form.id,
            "form_details": {
                "title": form.title,
                "form_type": form.form_type.name if form.form_type else None,
                "description": form.description,
                "version": form.version,
                "created_on": form.created_on,
                "workflow_name": workflow_name,
            },
            "sections": []
        }

        for section in sections:
            top_level_fields = FormFields.objects.filter(
                section=section,
                parent_field__isnull=True
            ).order_by("order")
            fields = [serialize_field(f) for f in top_level_fields]

            response_data["sections"].append({
                "section_id": section.id,
                "section_name": section.name,
                "dependency": section.dependency or {},
                "fields": fields
            })

        logger.info(f"User {request.user.id} retrieved form fields for form {form_id}")

        return api_response(
            data=response_data,
            message="Form fields retrieved successfully"
        )
    except Exception as e:
        logger.exception("Error retrieving form fields: %s", e)
        return api_response(
            message="Error retrieving form fields",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============== Form With Sections View ==============

# @form_with_sections_list_swagger()
# @api_view(['GET', 'POST'])
# @permission_classes([IsAuthenticated])
# def form_with_sections_list(request):
#     """
#     Get forms with their sections.

#     GET/POST /forms/with_sections/

#     Query Parameters:
#     - search: Search by form title
#     """
#     try:
#         query = Q(is_deleted=False)

#         search_term = request.GET.get('search') or request.data.get('search')
#         if search_term:
#             query &= Q(title__icontains=search_term)

#         forms = Form.objects.filter(query).order_by('-id')

#         response_data = []
#         for form in forms:
#             sections = FormSections.objects.filter(form=form).order_by("id")
#             section_list = [
#                 {
#                     "section_id": section.id,
#                     "section_name": section.name
#                 }
#                 for section in sections
#             ]
#             if section_list:
#                 response_data.append({
#                     "id": form.id,
#                     "name": form.title,
#                     "sections": section_list
#                 })

#         logger.info(f"User {request.user.id} retrieved forms with sections")

#         return api_response(
#             data=response_data,
#             message="Forms retrieved successfully"
#         )
#     except Exception as e:
#         logger.exception("Error retrieving forms with sections: %s", e)
#         return api_response(
#             message="Error retrieving forms",
#             errors={"detail": str(e)},
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dynamic_forms_list(request):
    """
    Get dynamic forms as a simple list for dropdowns/selects(for dynamic fields).

    GET /forms/list/

    Query Parameters:
    - form_type_id: Filter by form type (unique_code or UUID)
    - form_type_name: Filter by form type name (case-insensitive)
    - search: Search by title
    - is_completed: Filter by completion status (default: true)
    - main_process: Filter by main process UUID
    - criteria: Filter by criteria UUID
    - location: Filter by location UUID

    Returns:
    - data: List of forms directly (no wrapper object)
    """
    try:
        query = Q(effective_end_date__isnull=True)

        # Search filter
        search_title = request.GET.get("search", "").strip()
        if search_title:
            query &= Q(title__icontains=search_title)

        # Completion filter (default to True for dropdowns)
        is_completed_param = request.GET.get("is_completed", "true")
        if is_completed_param.lower() == "true":
            query &= Q(is_completed=True)
        elif is_completed_param.lower() == "false":
            query &= Q(is_completed=False)

        # Form type filter - support unique_code, UUID, or name
        form_type_id = request.GET.get("form_type_id")
        form_type_name = request.GET.get("form_type_name")

        if form_type_id or form_type_name:
            form_type_obj = None

            if form_type_id:
                # Try lookup by unique_code first
                form_type_obj = FormType.objects.filter(
                    unique_code=form_type_id,
                    effective_end_date__isnull=True
                ).first()

                # Fallback to UUID
                if not form_type_obj:
                    form_type_obj = FormType.objects.filter(
                        id=form_type_id,
                        effective_end_date__isnull=True
                    ).first()

            elif form_type_name:
                # Lookup by name (case-insensitive)
                form_type_obj = FormType.objects.filter(
                    name__iexact=form_type_name,
                    effective_end_date__isnull=True
                ).first()

            if form_type_obj:
                query &= Q(form_type_id=form_type_obj.id)
            else:
                # If form type not found, return empty results
                return api_response(
                    data=[],
                    message="FormType not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

        # Filter by main_process
        main_process_id = request.GET.get("main_process")
        if main_process_id:
            main_process_obj = MainProcess.objects.filter(
                id=main_process_id,
                effective_end_date__isnull=True
            ).first()
            if main_process_obj:
                query &= Q(main_process_id=main_process_obj.id)
            else:
                return api_response(
                    data=[],
                    message="Main process not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

        # Filter by criteria
        criteria_id = request.GET.get("criteria")
        if criteria_id:
            criteria_obj = Criteria.objects.filter(
                id=criteria_id,
                effective_end_date__isnull=True
            ).first()
            if criteria_obj:
                query &= Q(criteria_id=criteria_obj.id)
            else:
                return api_response(
                    data=[],
                    message="Criteria not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

        # Filter by location
        location_id = request.GET.get("location")
        if location_id:
            location_obj = Location.objects.filter(
                id=location_id,
                effective_end_date__isnull=True
            ).first()
            if location_obj:
                query &= Q(location_id=location_obj.id)
            else:
                return api_response(
                    data=[],
                    message="Location not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

        # Get all forms matching the query
        all_forms = Form.objects.filter(query)

        # Group by root and find latest version IDs
        latest_form_ids = {}
        for form in all_forms.order_by('version'):
            root_id = form.root_form_id if form.root_form_id else form.id
            latest_form_ids[root_id] = form.id

        # Filter to get only latest versions
        latest_forms = Form.objects.filter(
            id__in=latest_form_ids.values()
        ).select_related(
            'form_type', 'main_process', 'criteria', 'location'
        ).order_by("-id")

        # Build response list directly
        response_data = []
        for form in latest_forms:
            # Get all versions for this root form
            root_id = form.root_form_id or form.id
            all_version_forms = Form.objects.filter(
                Q(root_form_id=root_id) | Q(id=root_id),
                effective_end_date__isnull=True
            ).order_by("version")

            all_versions = [
                {
                    "id": v.id,
                    "version": v.version,
                    "unique_code": v.unique_code
                }
                for v in all_version_forms
            ]

            response_data.append({
                "id": form.unique_code,
                "version_id": str(form.id),
                "name": form.title,
                "title": form.title,
                "type": form.form_type.name if form.form_type else None,
                "description": form.description,
                "is_completed": form.is_completed,
                "version": form.version,
                "all_versions": all_versions,
                "main_process": {
                    "id": str(form.main_process.id),
                    "name": form.main_process.name
                } if form.main_process else None,
                "criteria": {
                    "id": str(form.criteria.id),
                    "name": form.criteria.name
                } if form.criteria else None,
                "location": {
                    "id": str(form.location.id),
                    "name": form.location.location_name
                } if form.location else None,
                "created_on": format_user_timezone(form.created_on) if form.created_on else None,
                "updated_on": format_user_timezone(form.updated_on) if hasattr(form, 'updated_on') and form.updated_on else None,
            })

        logger.info(f"User {request.user.id} retrieved dynamic forms list")

        return api_response(
            data=response_data,
            message="Forms retrieved successfully"
        )
    except Exception as e:
        logger.exception("Error retrieving forms list: %s", e)
        return api_response(
            message="Error retrieving forms",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@form_with_sections_list_swagger()
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
# @cache_response(max_age=600)  # Cache for 10 minutes - forms with sections
def form_with_sections_list(request):
    """
    Get forms with their sections (latest versions only).

    GET/POST /forms/with_sections/

    Query Parameters:
    - search: Search by form title
    
    Response includes:
    - Latest version of each form
    - All versions with their respective sections
    """
    try:
        query = Q(effective_end_date__isnull=True)

        search_term = request.GET.get('search') or request.data.get('search')
        if search_term:
            query &= Q(title__icontains=search_term)

        # Get all forms matching the query
        all_forms = Form.objects.filter(query)

        # Group by root and find latest version IDs
        latest_form_ids = {}
        for form in all_forms.order_by('version'):
            root_id = form.root_form_id if form.root_form_id else form.id
            # Keep overwriting with higher versions
            latest_form_ids[root_id] = form.id

        # Filter to get only latest versions
        latest_forms = Form.objects.filter(
            id__in=latest_form_ids.values()
        ).order_by('-id')

        response_data = []
        for form in latest_forms:
            sections = FormSections.objects.filter(form=form).order_by("id")
            section_list = [
                {
                    "section_id": section.id,
                    "section_name": section.name
                }
                for section in sections
            ]
            
            if section_list:
                # Get all versions for this root form
                root_id = form.root_form_id or form.id
                all_version_forms = Form.objects.filter(
                    Q(root_form_id=root_id) | Q(id=root_id),
                    effective_end_date__isnull=True
                ).order_by("version")

                version_list = []
                for version_form in all_version_forms:
                    # Get sections for each version
                    version_sections = FormSections.objects.filter(
                        form=version_form
                    ).order_by("id")
                    version_section_list = [
                        {
                            "section_id": section.id,
                            "section_name": section.name
                        }
                        for section in version_sections
                    ]

                    version_list.append({
                        "id": version_form.id,
                        "version": version_form.version,
                        "name": version_form.title,
                        "sections": version_section_list
                    })

                response_data.append({
                    "id": form.id,
                    "name": form.title,
                    "version": form.version,
                    "all_versions": version_list,
                    "sections": section_list
                })

        logger.info(f"User {request.user.id} retrieved forms with sections")

        return api_response(
            data=response_data,
            message="Forms retrieved successfully"
        )
    except Exception as e:
        logger.exception("Error retrieving forms with sections: %s", e)
        return api_response(
            message="Error retrieving forms",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )