from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

# Response schemas
FORM_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Form ID"),
        'title': openapi.Schema(type=openapi.TYPE_STRING, description="Form title"),
        'form_type': openapi.Schema(type=openapi.TYPE_STRING, description="Form type name"),
        'description': openapi.Schema(type=openapi.TYPE_STRING, description="Form description"),
        'version': openapi.Schema(type=openapi.TYPE_INTEGER, description="Form version"),
        'is_completed': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Whether form is completed"),
    }
)

DYNAMIC_FORMS_RESPONSE = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'forms': openapi.Schema(type=openapi.TYPE_ARRAY, items=FORM_SCHEMA, description="List of forms"),
        'obj_count': openapi.Schema(type=openapi.TYPE_INTEGER, description="Total count"),
        'max_pages': openapi.Schema(type=openapi.TYPE_INTEGER, description="Maximum pages"),
        'max_rows': openapi.Schema(type=openapi.TYPE_INTEGER, description="Rows per page"),
    }
)

FORM_FIELD_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'field_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Field ID"),
        'label': openapi.Schema(type=openapi.TYPE_STRING, description="Field label"),
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Field name"),
        'type_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Data type ID"),
        'type': openapi.Schema(type=openapi.TYPE_STRING, description="Data type name"),
        'required': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Whether field is required"),
        'end_point': openapi.Schema(type=openapi.TYPE_STRING, description="API endpoint for dynamic data"),
    }
)

FORM_FIELDS_RESPONSE = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'form_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Form ID"),
        'form_details': openapi.Schema(type=openapi.TYPE_OBJECT, description="Form details"),
        'sections': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'section_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'section_name': openapi.Schema(type=openapi.TYPE_STRING),
                    'fields': openapi.Schema(type=openapi.TYPE_ARRAY, items=FORM_FIELD_SCHEMA),
                }
            ),
            description="Form sections with fields"
        ),
    }
)

# Request schemas
FORM_CREATE_REQUEST = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['title', 'type_id'],
    properties={
        'title': openapi.Schema(type=openapi.TYPE_STRING, description="Title of the form"),
        'type_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the form type"),
        'desc': openapi.Schema(type=openapi.TYPE_STRING, description="Description"),
        'system_config': openapi.Schema(type=openapi.TYPE_OBJECT, description="System configuration"),
        'user_config': openapi.Schema(type=openapi.TYPE_OBJECT, description="User configuration"),
    }
)

FORM_FIELDS_CREATE_REQUEST = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['sections'],
    properties={
        'sections': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'section_name': openapi.Schema(type=openapi.TYPE_STRING, description="Section name"),
                    'fields': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                }
            ),
            description="List of sections with fields"
        ),
        'system_config': openapi.Schema(type=openapi.TYPE_OBJECT, description="System configuration"),
        'user_config': openapi.Schema(type=openapi.TYPE_OBJECT, description="User configuration"),
    }
)


# Decorator factories
def get_dynamic_forms_swagger():
    """Decorator for get_dynamic_forms view"""
    return swagger_auto_schema(
        method='get',
        operation_description="Get dynamic forms with pagination and filters.",
        manual_parameters=[
            openapi.Parameter('page_number', openapi.IN_QUERY, description="Page number (default: 1)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by title", type=openapi.TYPE_STRING),
            openapi.Parameter('is_completed', openapi.IN_QUERY, description="Filter by completion status", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('form_type_id', openapi.IN_QUERY, description="Filter by form type ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('workflow_type_id', openapi.IN_QUERY, description="Filter by workflow type ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('workflow_name_id', openapi.IN_QUERY, description="Filter by workflow ID", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response(description="Forms retrieved successfully", schema=DYNAMIC_FORMS_RESPONSE),
            500: "Server error"
        }
    )


def form_create_swagger():
    """Decorator for form_create view"""
    return swagger_auto_schema(
        method='post',
        operation_description="Create a new dynamic form.",
        request_body=FORM_CREATE_REQUEST,
        responses={
            201: openapi.Response(description="Form created successfully", schema=FORM_SCHEMA),
            400: "Validation failed",
            500: "Server error"
        }
    )


def form_detail_swagger():
    """Decorator for form_detail view"""
    return swagger_auto_schema(
        method='get',
        operation_description="Get a specific form by ID.",
        responses={
            200: openapi.Response(description="Form retrieved successfully", schema=FORM_SCHEMA),
            404: "Form not found",
            500: "Server error"
        }
    )


def forms_by_type_swagger():
    """Decorator for forms_by_type view"""
    return swagger_auto_schema(
        method='get',
        operation_description="Get forms filtered by type.",
        manual_parameters=[
            openapi.Parameter('type', openapi.IN_QUERY, description="Form type ID or name", type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by title", type=openapi.TYPE_STRING),
        ],
        responses={
            200: "Forms retrieved successfully",
            404: "Form type not found",
            500: "Server error"
        }
    )


def create_form_fields_swagger():
    """Decorator for create_form_fields view"""
    return swagger_auto_schema(
        method='post',
        operation_description="Create fields for a form. If form is linked to a workflow, creates a new version.",
        request_body=FORM_FIELDS_CREATE_REQUEST,
        responses={
            200: "Form fields updated successfully",
            201: "New form version created with fields",
            400: "Validation failed",
            404: "Form or field type not found",
            500: "Server error"
        }
    )


def get_form_fields_swagger():
    """Decorator for get_form_fields view"""
    return swagger_auto_schema(
        method='get',
        operation_description="Get all fields for a form.",
        responses={
            200: openapi.Response(description="Form fields retrieved successfully", schema=FORM_FIELDS_RESPONSE),
            404: "Form not found",
            500: "Server error"
        }
    )


SECTION_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'section_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Section ID"),
        'section_name': openapi.Schema(type=openapi.TYPE_STRING, description="Section name"),
    }
)

VERSION_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Form version ID"),
        'version': openapi.Schema(type=openapi.TYPE_INTEGER, description="Version number"),
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Form title"),
        'sections': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=SECTION_SCHEMA,
            description="Sections for this version"
        ),
    }
)

FORM_WITH_SECTIONS_RESPONSE = openapi.Schema(
    type=openapi.TYPE_ARRAY,
    items=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Latest form ID"),
            'name': openapi.Schema(type=openapi.TYPE_STRING, description="Form title"),
            'version': openapi.Schema(type=openapi.TYPE_INTEGER, description="Latest version number"),
            'all_versions': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=VERSION_SCHEMA,
                description="All versions of this form with their sections"
            ),
            'sections': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=SECTION_SCHEMA,
                description="Sections for the latest version"
            ),
        }
    )
)


def form_with_sections_list_swagger():
    """Decorator for form_with_sections_list view"""
    def decorator(func):
        func = swagger_auto_schema(
            method='post',
            operation_description="Get forms with their sections (latest versions only) using POST. Returns all versions with their respective sections.",
            request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'search': openapi.Schema(type=openapi.TYPE_STRING, description="Search by form title"),
                }
            ),
            responses={
                200: openapi.Response(
                    description="Forms retrieved successfully",
                    schema=FORM_WITH_SECTIONS_RESPONSE
                ),
                500: "Server error"
            }
        )(func)
        func = swagger_auto_schema(
            method='get',
            operation_description="Get forms with their sections (latest versions only). Returns all versions with their respective sections.",
            manual_parameters=[
                openapi.Parameter('search', openapi.IN_QUERY, description="Search by form title", type=openapi.TYPE_STRING),
            ],
            responses={
                200: openapi.Response(
                    description="Forms retrieved successfully",
                    schema=FORM_WITH_SECTIONS_RESPONSE
                ),
                500: "Server error"
            }
        )(func)
        return func
    return decorator
