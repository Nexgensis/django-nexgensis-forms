from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

# Response schemas
FIELD_TYPE_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Field type ID"),
        'label': openapi.Schema(type=openapi.TYPE_STRING, description="Field type label/name"),
        'type_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Data type ID"),
        'type_name': openapi.Schema(type=openapi.TYPE_STRING, description="Data type name"),
        'validation_rules': openapi.Schema(type=openapi.TYPE_OBJECT, description="Validation rules JSON"),
        'dynamic': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Whether field fetches dynamic data"),
        'end_point': openapi.Schema(type=openapi.TYPE_STRING, description="API endpoint for dynamic data"),
    }
)

FIELD_TYPE_LIST_RESPONSE = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'field_types': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=FIELD_TYPE_SCHEMA,
            description="List of field types"
        ),
    }
)

# Request schemas
FIELD_TYPE_CREATE_REQUEST = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['label', 'type_id'],
    properties={
        'field_type_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID for updating existing field type (optional)"),
        'label': openapi.Schema(type=openapi.TYPE_STRING, description="Name of the field type"),
        'type_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the data type"),
        'validation_rules': openapi.Schema(type=openapi.TYPE_OBJECT, description="JSON object with validation rules"),
        'dynamic': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Whether field fetches dynamic data"),
        'end_point': openapi.Schema(type=openapi.TYPE_STRING, description="API endpoint for dynamic data"),
    }
)

FIELD_TYPE_UPDATE_REQUEST = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'label': openapi.Schema(type=openapi.TYPE_STRING, description="Name of the field type"),
        'type_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the data type"),
        'validation_rules': openapi.Schema(type=openapi.TYPE_OBJECT, description="JSON object with validation rules"),
        'dynamic': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Whether field fetches dynamic data"),
        'end_point': openapi.Schema(type=openapi.TYPE_STRING, description="API endpoint for dynamic data"),
    }
)


# Decorator factories
def field_type_list_swagger():
    """Decorator for field_type_list view"""
    return swagger_auto_schema(
        method='get',
        operation_description="Get all field types. Returns a list of all non-deleted field types.",
        responses={
            200: openapi.Response(description="Field types retrieved successfully", schema=FIELD_TYPE_LIST_RESPONSE),
            500: "Server error"
        }
    )


def field_type_create_swagger():
    """Decorator for field_type_create view"""
    return swagger_auto_schema(
        method='post',
        operation_description="Create a new field type or update existing one if field_type_id is provided.",
        request_body=FIELD_TYPE_CREATE_REQUEST,
        responses={
            200: openapi.Response(description="Field type updated successfully", schema=FIELD_TYPE_SCHEMA),
            201: openapi.Response(description="Field type created successfully", schema=FIELD_TYPE_SCHEMA),
            400: "Validation failed",
            404: "Field type not found (when updating)",
            500: "Server error"
        }
    )


def field_type_update_swagger():
    """Decorator for field_type_update view"""
    def decorator(func):
        func = swagger_auto_schema(
            method='patch',
            operation_description="Partially update an existing field type.",
            request_body=FIELD_TYPE_UPDATE_REQUEST,
            responses={
                200: openapi.Response(description="Field type updated successfully", schema=FIELD_TYPE_SCHEMA),
                400: "Validation failed",
                404: "Field type not found",
                500: "Server error"
            }
        )(func)
        func = swagger_auto_schema(
            method='put',
            operation_description="Update an existing field type.",
            request_body=FIELD_TYPE_CREATE_REQUEST,
            responses={
                200: openapi.Response(description="Field type updated successfully", schema=FIELD_TYPE_SCHEMA),
                400: "Validation failed",
                404: "Field type not found",
                500: "Server error"
            }
        )(func)
        return func
    return decorator


def field_type_delete_swagger():
    """Decorator for field_type_delete view"""
    return swagger_auto_schema(
        method='delete',
        operation_description="Delete a field type (soft delete).",
        responses={
            200: "Field type deleted successfully",
            404: "Field type not found or already deleted",
            500: "Server error"
        }
    )
