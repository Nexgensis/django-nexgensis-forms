from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

# Response schemas
FOCUS_AREA_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_STRING, description="Focus area UUID"),
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Focus area name"),
    }
)

FOCUS_AREA_LIST_RESPONSE = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'focus_areas': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=FOCUS_AREA_SCHEMA,
            description="List of focus areas"
        ),
    }
)

# Request schemas
FOCUS_AREA_CREATE_REQUEST = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['name'],
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Name of the focus area"),
    }
)

FOCUS_AREA_UPDATE_REQUEST = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Name of the focus area"),
    }
)


# Decorator factories
def focus_area_list_swagger():
    """Decorator for focus_area_list view"""
    return swagger_auto_schema(
        method='get',
        operation_description="Get all active focus areas. Returns a list of all focus areas.",
        responses={
            200: openapi.Response(description="Focus areas retrieved successfully", schema=FOCUS_AREA_LIST_RESPONSE),
            500: "Server error"
        }
    )


def focus_area_create_swagger():
    """Decorator for focus_area_create view"""
    return swagger_auto_schema(
        method='post',
        operation_description="Create a new focus area.",
        request_body=FOCUS_AREA_CREATE_REQUEST,
        responses={
            201: openapi.Response(description="Focus area created successfully", schema=FOCUS_AREA_SCHEMA),
            400: "Validation failed",
            500: "Server error"
        }
    )


def focus_area_detail_swagger():
    """Decorator for focus_area_detail view"""
    return swagger_auto_schema(
        method='get',
        operation_description="Get details of a specific focus area.",
        responses={
            200: openapi.Response(description="Focus area retrieved successfully", schema=FOCUS_AREA_SCHEMA),
            404: "Focus area not found",
            500: "Server error"
        }
    )


def focus_area_update_swagger():
    """Decorator for focus_area_update view"""
    def decorator(func):
        func = swagger_auto_schema(
            method='patch',
            operation_description="Partially update an existing focus area.",
            request_body=FOCUS_AREA_UPDATE_REQUEST,
            responses={
                200: openapi.Response(description="Focus area updated successfully", schema=FOCUS_AREA_SCHEMA),
                400: "Validation failed",
                404: "Focus area not found",
                500: "Server error"
            }
        )(func)
        func = swagger_auto_schema(
            method='put',
            operation_description="Update an existing focus area.",
            request_body=FOCUS_AREA_CREATE_REQUEST,
            responses={
                200: openapi.Response(description="Focus area updated successfully", schema=FOCUS_AREA_SCHEMA),
                400: "Validation failed",
                404: "Focus area not found",
                500: "Server error"
            }
        )(func)
        return func
    return decorator


def focus_area_delete_swagger():
    """Decorator for focus_area_delete view"""
    return swagger_auto_schema(
        method='delete',
        operation_description="Delete a focus area (soft delete).",
        responses={
            200: "Focus area deleted successfully",
            404: "Focus area not found",
            500: "Server error"
        }
    )
