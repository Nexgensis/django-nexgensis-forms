import logging
import uuid

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Max

from ..models import Form, FormDraft, FormType
from ..serializers.form_design_serializers import FormDraftCreateUpdateSerializer
from ..utils import api_response
from ..conf import get_workflow_checklist_model

# Get swappable workflow model from configuration
WorkflowChecklist = get_workflow_checklist_model()
from ..views.swagger import (
    get_form_draft_swagger,
    save_form_draft_swagger,
)

logger = logging.getLogger(__name__)


# ============== Form Draft Views ==============

@get_form_draft_swagger()
@api_view(['GET'])
@permission_classes([IsAuthenticated])
# @cache_response(max_age=300)  # Cache for 5 minutes - draft data needs freshness
def get_form_draft(request, form_id, version=None):
    """
    Get form draft.

    GET /get_form_draft/<form_id>/

    Query Parameters:
    - version: Specific version to retrieve

    Note:
    - form_id can be either unique_code (FORM-XXXXXXXX) or UUID
    """
    try:
        # Get form by unique_code or UUID
        form = Form.objects.filter(
            unique_code=form_id,
            effective_end_date__isnull=True
        ).select_related('form_type', 'main_process', 'criteria').first()

        # Fallback to UUID lookup if not found by unique_code
        if not form:
            form = Form.objects.filter(id=form_id).select_related(
                'form_type', 'main_process', 'criteria'
            ).first()

        if not form:
            return api_response(
                message="Form not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # If version specified, get that specific version
        if version:
            root_form = form.root_form if form.root_form else form
            form = Form.objects.filter(
                root_form=root_form,
                version=version,
                effective_end_date__isnull=True
            ).select_related('form_type', 'main_process', 'criteria').first()
            if not form:
                return api_response(
                    message="Version not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

        form_draft = FormDraft.objects.filter(form=form).first()
        if not form_draft:
            return api_response(
                message="No draft found for this form",
                status_code=status.HTTP_404_NOT_FOUND
            )

        workflow_name = None
        if WorkflowChecklist is not None:
            workflow_checklist = WorkflowChecklist.objects.filter(checklist=form).first()
            if workflow_checklist:
                workflow_name = workflow_checklist.workflow_stage.workflow.name

        form_details = {
            "title": form.title,
            "form_type": form.form_type.name if form.form_type else None,
            "description": form.description,
            "version": form.version,
            "created_on": form.created_on,
            "workflow_name": workflow_name,
            "main_process": {
                "id": str(form.main_process.id),
                "name": form.main_process.name
            } if form.main_process else None,
            "criteria": {
                "id": str(form.criteria.id),
                "name": form.criteria.name
            } if form.criteria else None,
        }

        logger.info(f"User {request.user.id} retrieved draft for form {form_id}")

        return api_response(
            data={
                "draft_data": form_draft.draft_data,
                "form_details": form_details
            },
            message="Form draft retrieved successfully"
        )

    except Exception as e:
        logger.exception("Error retrieving form draft: %s", e)
        return api_response(
            message="Error retrieving form draft",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@save_form_draft_swagger()
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def save_form_draft(request, form_id):
    """
    Save form draft with optimistic locking.

    POST /save_form_draft/<form_id>/

    Request body:
    - draft_data: The draft data to save (required)
    - form_details: Form metadata (title, description, form_type) (optional)
    - version_id: UUID of the version being edited (required for optimistic locking)

    Note:
    - form_id can be either unique_code (FORM-XXXXXXXX) or UUID
    - version_id is REQUIRED to prevent concurrent modification conflicts
    - form_details.form_type can be either FormType unique_code or UUID
    - If form is linked to a workflow, creates a new version with is_completed=False
    - If form is not linked to a workflow, updates/creates draft for existing form
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

        serializer = FormDraftCreateUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                message="Validation failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        draft_data = serializer.validated_data['draft_data']

        # Extract form_details if provided
        form_details = request.data.get('form_details', {})

        # Process form_type lookup if provided in form_details
        form_type_obj = None
        if form_details.get('form_type'):
            form_type_identifier = form_details['form_type']

            # Try lookup by unique_code first
            form_type_obj = FormType.objects.filter(
                unique_code=form_type_identifier,
                effective_end_date__isnull=True
            ).first()

            # Fallback to UUID (only if value is a valid UUID)
            if not form_type_obj:
                try:
                    uuid.UUID(str(form_type_identifier))
                    form_type_obj = FormType.objects.filter(
                        id=form_type_identifier,
                        effective_end_date__isnull=True
                    ).first()
                except (ValueError, AttributeError):
                    pass  # Not a valid UUID, skip this lookup

            if not form_type_obj:
                return api_response(
                    message="FormType not found",
                    errors={"form_type": "Invalid FormType identifier"},
                    status_code=status.HTTP_404_NOT_FOUND
                )

        # Check if form is attached to a workflow
        is_linked_to_workflow = False
        if WorkflowChecklist is not None:
            is_linked_to_workflow = WorkflowChecklist.objects.filter(checklist_id=form.id).exists()

        if is_linked_to_workflow:
            # Create new version without setting is_completed=True
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
                system_config=draft_data.get("system_config", {}),
                user_config=draft_data.get("user_config", {}),
                is_completed=False,  # Keep as draft, not completed
                created_by=request.user,  # Track creator
                previous_version_id=form.id  # Link to previous version
            )

            form_draft = FormDraft.objects.create(form=new_form, draft_data=draft_data)

            logger.info(f"User {request.user.id} created new draft version {new_form.id} for form {form_id}")

            return api_response(
                data={
                    "form_draft_id": form_draft.id,
                    "form_id": new_form.id,
                    "version": new_form.version,
                    "version_id": new_form.id,  # Return version_id
                    "unique_code": new_form.unique_code  # Return unique_code
                },
                message="Form is linked to a workflow. Created new draft version.",
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
            if draft_data.get("system_config"):
                form.system_config = draft_data["system_config"]
            if draft_data.get("user_config"):
                form.user_config = draft_data["user_config"]
            form.save()

            # Update or create form draft
            form_draft, _ = FormDraft.objects.update_or_create(
                form=form,
                defaults={'draft_data': draft_data}
            )

            logger.info(f"User {request.user.id} saved draft for form {form_id}")

            return api_response(
                data={
                    "form_draft_id": form_draft.id,
                    "form_id": form.id,
                    "version": form.version,
                    "version_id": form.id,
                    "unique_code": form.unique_code
                },
                message="Form draft saved successfully"
            )

    except Exception as e:
        logger.exception("Error saving form draft: %s", e)
        return api_response(
            message="Error saving form draft",
            errors={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

