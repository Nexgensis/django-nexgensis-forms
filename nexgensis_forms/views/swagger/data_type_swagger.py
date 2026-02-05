from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

# Response schemas
DATA_TYPE_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Data type ID"),
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Data type name"),
        'validation_rules': openapi.Schema(type=openapi.TYPE_OBJECT, description="Validation rules JSON"),
    }
)

DATA_TYPE_LIST_RESPONSE = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'data_types': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=DATA_TYPE_SCHEMA,
            description="List of data types"
        ),
    }
)

# Request schemas
DATA_TYPE_CREATE_REQUEST = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['name'],
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Name of the data type"),
        'validation_rules': openapi.Schema(type=openapi.TYPE_OBJECT, description="JSON object with validation rules"),
    }
)

DATA_TYPE_UPDATE_REQUEST = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Name of the data type"),
        'validation_rules': openapi.Schema(type=openapi.TYPE_OBJECT, description="JSON object with validation rules"),
    }
)


# Decorator factories
def data_type_list_swagger():
    """Decorator for data_type_list view"""
    return swagger_auto_schema(
        method='get',
        operation_description="Get all data types. Returns a list of all data types with id, name, and validation_rules.",
        responses={
            200: openapi.Response(description="Data types retrieved successfully", schema=DATA_TYPE_LIST_RESPONSE),
            500: "Server error"
        }
    )


def data_type_create_swagger():
    """Decorator for data_type_create view"""
    return swagger_auto_schema(
        method='post',
        operation_description="Create a new data type.",
        request_body=DATA_TYPE_CREATE_REQUEST,
        responses={
            201: openapi.Response(description="Data type created successfully", schema=DATA_TYPE_SCHEMA),
            400: "Validation failed",
            500: "Server error"
        }
    )


def data_type_update_swagger():
    """Decorator for data_type_update view"""
    def decorator(func):
        func = swagger_auto_schema(
            method='patch',
            operation_description="Partially update an existing data type.",
            request_body=DATA_TYPE_UPDATE_REQUEST,
            responses={
                200: openapi.Response(description="Data type updated successfully", schema=DATA_TYPE_SCHEMA),
                400: "Validation failed",
                404: "Data type not found",
                500: "Server error"
            }
        )(func)
        func = swagger_auto_schema(
            method='put',
            operation_description="Update an existing data type.",
            request_body=DATA_TYPE_CREATE_REQUEST,
            responses={
                200: openapi.Response(description="Data type updated successfully", schema=DATA_TYPE_SCHEMA),
                400: "Validation failed",
                404: "Data type not found",
                500: "Server error"
            }
        )(func)
        return func
    return decorator


def data_type_delete_swagger():
    """Decorator for data_type_delete view"""
    return swagger_auto_schema(
        method='delete',
        operation_description="Delete a data type. Will fail if the data type is referenced by any FieldType.",
        responses={
            200: "Data type deleted successfully",
            400: "Data type is referenced by existing field types",
            404: "Data type not found",
            500: "Server error"
        }
    )
