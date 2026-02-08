from rest_framework.decorators import api_view
from django.db import transaction

from ..models import Form
from ..utils import api_response
from ..conf import get_workflow_checklist_model

# Get swappable workflow model from configuration
WorkflowChecklist = get_workflow_checklist_model()
from ..views.swagger import delete_form_swagger
import logging

logger = logging.getLogger(__name__)


# ============== Delete Form API ==============

@delete_form_swagger()
@api_view(["DELETE"])
@transaction.atomic
def delete_form(request, pk):
    """
    Delete a form by ID with soft/hard delete support.

    Note:
    - pk can be either unique_code (FORM-XXXXXXXX) or UUID
    """
    try:
        # Get form by unique_code or UUID
        form = Form.objects.filter(
            unique_code=pk,
            effective_end_date__isnull=True
        ).first()

        # Fallback to UUID lookup if not found by unique_code
        if not form:
            form = Form.objects.filter(id=pk, effective_end_date__isnull=True).first()

        if not form:
            return api_response(message="Form not found.", status_code=404)

        # Check if form is attached to any workflow (only if workflow model is configured)
        if WorkflowChecklist is not None:
            if WorkflowChecklist.objects.filter(
                checklist_id=form.id,
                workflow_stage__workflow__is_deleted=False
            ).exists():
                return api_response(
                    message="This form cannot be deleted because it is linked to a workflow.",
                    status_code=400
                )

        # Use TimestampedModel2's built-in soft delete (sets effective_end_date)
        form.delete()

        return api_response(message="Form and related data deleted successfully.")

    except Exception as e:
        logger.exception("Error deleting form with ID %s: %s", pk, e)
        return api_response(message=str(e), status_code=500)
