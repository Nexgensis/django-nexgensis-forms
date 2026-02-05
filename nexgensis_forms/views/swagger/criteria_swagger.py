from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

# Response schemas
CRITERIA_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_STRING, description="Criteria UUID"),
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Criteria name"),
    }
)

CRITERIA_LIST_RESPONSE = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'criteria': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=CRITERIA_SCHEMA,
            description="List of criteria"
        ),
    }
)

# Request schemas
CRITERIA_CREATE_REQUEST = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['name'],
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Name of the criteria"),
    }
)

CRITERIA_UPDATE_REQUEST = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Name of the criteria"),
    }
)


# Decorator factories
def criteria_list_swagger():
    """Decorator for criteria_list view"""
    return swagger_auto_schema(
        method='get',
        operation_description="Get all active criteria. Returns a list of all criteria.",
        responses={
            200: openapi.Response(description="Criteria retrieved successfully", schema=CRITERIA_LIST_RESPONSE),
            500: "Server error"
        }
    )


def criteria_create_swagger():
    """Decorator for criteria_create view"""
    return swagger_auto_schema(
        method='post',
        operation_description="Create a new criteria.",
        request_body=CRITERIA_CREATE_REQUEST,
        responses={
            201: openapi.Response(description="Criteria created successfully", schema=CRITERIA_SCHEMA),
            400: "Validation failed",
            500: "Server error"
        }
    )


def criteria_detail_swagger():
    """Decorator for criteria_detail view"""
    return swagger_auto_schema(
        method='get',
        operation_description="Get details of a specific criteria.",
        responses={
            200: openapi.Response(description="Criteria retrieved successfully", schema=CRITERIA_SCHEMA),
            404: "Criteria not found",
            500: "Server error"
        }
    )


def criteria_update_swagger():
    """Decorator for criteria_update view"""
    def decorator(func):
        func = swagger_auto_schema(
            method='patch',
            operation_description="Partially update an existing criteria.",
            request_body=CRITERIA_UPDATE_REQUEST,
            responses={
                200: openapi.Response(description="Criteria updated successfully", schema=CRITERIA_SCHEMA),
                400: "Validation failed",
                404: "Criteria not found",
                500: "Server error"
            }
        )(func)
        func = swagger_auto_schema(
            method='put',
            operation_description="Update an existing criteria.",
            request_body=CRITERIA_CREATE_REQUEST,
            responses={
                200: openapi.Response(description="Criteria updated successfully", schema=CRITERIA_SCHEMA),
                400: "Validation failed",
                404: "Criteria not found",
                500: "Server error"
            }
        )(func)
        return func
    return decorator


def criteria_delete_swagger():
    """Decorator for criteria_delete view"""
    return swagger_auto_schema(
        method='delete',
        operation_description="Delete a criteria (soft delete).",
        responses={
            200: "Criteria deleted successfully",
            404: "Criteria not found",
            500: "Server error"
        }
    )
