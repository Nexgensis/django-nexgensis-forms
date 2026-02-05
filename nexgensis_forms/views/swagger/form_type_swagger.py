from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

# Response schemas
FORM_TYPE_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Form type ID"),
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Form type name"),
        'description': openapi.Schema(type=openapi.TYPE_STRING, description="Form type description"),
        'parent_form_type': openapi.Schema(type=openapi.TYPE_INTEGER, description="Parent form type ID"),
    }
)

FORM_TYPE_LIST_RESPONSE = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'data': openapi.Schema(type=openapi.TYPE_ARRAY, items=FORM_TYPE_SCHEMA, description="List of form types"),
        'pagination': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'current_page': openapi.Schema(type=openapi.TYPE_INTEGER),
                'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER),
                'total_records': openapi.Schema(type=openapi.TYPE_INTEGER),
                'page_size': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        ),
    }
)

# Request schemas
FORM_TYPE_CREATE_REQUEST = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['name'],
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Name of the form type (max 100 chars)"),
        'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description"),
        'parent_form_type_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of parent form type"),
    }
)

FORM_TYPE_UPDATE_REQUEST = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Name of the form type"),
        'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description"),
        'parent_form_type_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of parent form type (set to null to remove parent)"),
    }
)


# Decorator factories
def form_type_list_swagger():
    """Decorator for form_type_list view"""
    return swagger_auto_schema(
        method='get',
        operation_description="Get all form types with optional pagination. Use 'source=dropdown' for dropdown data (page_size=1000).",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by name", type=openapi.TYPE_STRING),
            openapi.Parameter('order_by', openapi.IN_QUERY, description="Field to order by (default: 'name')", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number (enables pagination)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Records per page (default: 8)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('source', openapi.IN_QUERY, description="Use 'dropdown' for dropdown source", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(description="Form types retrieved successfully", schema=FORM_TYPE_LIST_RESPONSE),
            500: "Server error"
        }
    )


def form_type_create_swagger():
    """Decorator for form_type_create view"""
    return swagger_auto_schema(
        method='post',
        operation_description="Create a new form type.",
        request_body=FORM_TYPE_CREATE_REQUEST,
        responses={
            201: openapi.Response(description="Form type created successfully", schema=FORM_TYPE_SCHEMA),
            400: "Validation failed",
            500: "Server error"
        }
    )


def form_type_detail_swagger():
    """Decorator for form_type_detail view"""
    return swagger_auto_schema(
        method='get',
        operation_description="Get a specific form type by ID.",
        responses={
            200: openapi.Response(description="Form type retrieved successfully", schema=FORM_TYPE_SCHEMA),
            404: "Form type not found",
            500: "Server error"
        }
    )


def form_type_update_swagger():
    """Decorator for form_type_update view"""
    def decorator(func):
        func = swagger_auto_schema(
            method='patch',
            operation_description="Partially update an existing form type.",
            request_body=FORM_TYPE_UPDATE_REQUEST,
            responses={
                200: openapi.Response(description="Form type updated successfully", schema=FORM_TYPE_SCHEMA),
                400: "Validation failed",
                404: "Form type not found",
                500: "Server error"
            }
        )(func)
        func = swagger_auto_schema(
            method='put',
            operation_description="Update an existing form type.",
            request_body=FORM_TYPE_CREATE_REQUEST,
            responses={
                200: openapi.Response(description="Form type updated successfully", schema=FORM_TYPE_SCHEMA),
                400: "Validation failed",
                404: "Form type not found",
                500: "Server error"
            }
        )(func)
        return func
    return decorator


def form_type_delete_swagger():
    """Decorator for form_type_delete view"""
    return swagger_auto_schema(
        method='delete',
        operation_description="Delete a form type (soft delete). Will fail if the form type has associated forms or sub-types.",
        responses={
            200: "Form type deleted successfully",
            400: "Form type is referenced by forms or has sub-types",
            404: "Form type not found",
            500: "Server error"
        }
    )
