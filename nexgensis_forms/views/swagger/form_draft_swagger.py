from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

# Response schemas
FORM_DRAFT_RESPONSE = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'draft_data': openapi.Schema(type=openapi.TYPE_OBJECT, description="Form draft data"),
        'form_details': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description="Form title"),
                'form_type': openapi.Schema(type=openapi.TYPE_STRING, description="Form type name"),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description="Form description"),
                'version': openapi.Schema(type=openapi.TYPE_INTEGER, description="Form version"),
                'created_on': openapi.Schema(type=openapi.TYPE_STRING, description="Creation timestamp"),
                'workflow_name': openapi.Schema(type=openapi.TYPE_STRING, description="Linked workflow name"),
            }
        ),
    }
)

SAVE_DRAFT_RESPONSE = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'form_draft_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Draft ID"),
        'form_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Form ID"),
        'version': openapi.Schema(type=openapi.TYPE_INTEGER, description="Form version"),
    }
)

# Request schemas
SAVE_DRAFT_REQUEST = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['draft_data'],
    properties={
        'draft_data': openapi.Schema(type=openapi.TYPE_OBJECT, description="The draft data to save"),
    }
)


# Decorator factories
def get_form_draft_swagger():
    """Decorator for get_form_draft view"""
    return swagger_auto_schema(
        method='get',
        operation_description="Get form draft. Optionally retrieve a specific version.",
        manual_parameters=[
            openapi.Parameter('version', openapi.IN_QUERY, description="Specific version to retrieve", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response(description="Form draft retrieved successfully", schema=FORM_DRAFT_RESPONSE),
            404: "Form or draft not found",
            500: "Server error"
        }
    )


def save_form_draft_swagger():
    """Decorator for save_form_draft view"""
    return swagger_auto_schema(
        method='post',
        operation_description="Save form draft. If form is linked to a workflow, creates a new version with is_completed=False. Otherwise updates/creates draft for existing form.",
        request_body=SAVE_DRAFT_REQUEST,
        responses={
            200: openapi.Response(description="Form draft saved successfully", schema=SAVE_DRAFT_RESPONSE),
            201: openapi.Response(description="New draft version created", schema=SAVE_DRAFT_RESPONSE),
            400: "Validation failed",
            404: "Form not found",
            500: "Server error"
        }
    )
