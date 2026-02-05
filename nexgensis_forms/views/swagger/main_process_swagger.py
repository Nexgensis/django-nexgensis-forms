from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

# Response schemas
MAIN_PROCESS_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_STRING, description="Main process UUID"),
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Main process name"),
    }
)

MAIN_PROCESS_LIST_RESPONSE = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'main_processes': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=MAIN_PROCESS_SCHEMA,
            description="List of main processes"
        ),
    }
)

# Request schemas
MAIN_PROCESS_CREATE_REQUEST = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['name'],
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Name of the main process"),
    }
)

MAIN_PROCESS_UPDATE_REQUEST = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Name of the main process"),
    }
)


# Decorator factories
def main_process_list_swagger():
    """Decorator for main_process_list view"""
    return swagger_auto_schema(
        method='get',
        operation_description="Get all active main processes. Returns a list of all main processes.",
        responses={
            200: openapi.Response(description="Main processes retrieved successfully", schema=MAIN_PROCESS_LIST_RESPONSE),
            500: "Server error"
        }
    )


def main_process_create_swagger():
    """Decorator for main_process_create view"""
    return swagger_auto_schema(
        method='post',
        operation_description="Create a new main process.",
        request_body=MAIN_PROCESS_CREATE_REQUEST,
        responses={
            201: openapi.Response(description="Main process created successfully", schema=MAIN_PROCESS_SCHEMA),
            400: "Validation failed",
            500: "Server error"
        }
    )


def main_process_detail_swagger():
    """Decorator for main_process_detail view"""
    return swagger_auto_schema(
        method='get',
        operation_description="Get details of a specific main process.",
        responses={
            200: openapi.Response(description="Main process retrieved successfully", schema=MAIN_PROCESS_SCHEMA),
            404: "Main process not found",
            500: "Server error"
        }
    )


def main_process_update_swagger():
    """Decorator for main_process_update view"""
    def decorator(func):
        func = swagger_auto_schema(
            method='patch',
            operation_description="Partially update an existing main process.",
            request_body=MAIN_PROCESS_UPDATE_REQUEST,
            responses={
                200: openapi.Response(description="Main process updated successfully", schema=MAIN_PROCESS_SCHEMA),
                400: "Validation failed",
                404: "Main process not found",
                500: "Server error"
            }
        )(func)
        func = swagger_auto_schema(
            method='put',
            operation_description="Update an existing main process.",
            request_body=MAIN_PROCESS_CREATE_REQUEST,
            responses={
                200: openapi.Response(description="Main process updated successfully", schema=MAIN_PROCESS_SCHEMA),
                400: "Validation failed",
                404: "Main process not found",
                500: "Server error"
            }
        )(func)
        return func
    return decorator


def main_process_delete_swagger():
    """Decorator for main_process_delete view"""
    return swagger_auto_schema(
        method='delete',
        operation_description="Delete a main process (soft delete).",
        responses={
            200: "Main process deleted successfully",
            404: "Main process not found",
            500: "Server error"
        }
    )
