from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


# Decorator factories
def delete_form_swagger():
    """Decorator for delete_form view"""
    return swagger_auto_schema(
        method='delete',
        operation_description="Delete a form by ID. Performs soft delete if the model supports it, otherwise hard delete. Will fail if the form is linked to a workflow.",
        responses={
            200: "Form and related data deleted successfully",
            400: "Form is linked to a workflow and cannot be deleted",
            404: "Form not found",
            500: "Server error"
        }
    )
