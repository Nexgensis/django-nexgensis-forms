from django.urls import path
from .views.data_type_views import (
    data_type_list, data_type_create,
    data_type_update, data_type_delete
)
from .views.form_type_views import (
    form_type_list, form_type_create, form_type_detail,
    form_type_update, form_type_delete
)
from .views.field_type_views import (
    field_type_list, field_type_create,
    field_type_update, field_type_delete
)
from .views.form_design_views import (
    get_dynamic_forms, get_dynamic_forms_list, form_create, form_detail, forms_by_type,
    create_form_fields, get_form_fields, form_with_sections_list
)
from .views.form_draft_views import (
    get_form_draft, save_form_draft
)
from .views.form_views import delete_form
from .views.bulk_upload_forms_views import (
    bulk_upload_forms, download_forms_template, export_forms_data
)
from .views.main_process_views import (
    main_process_list, main_process_create, main_process_detail,
    main_process_update, main_process_delete
)
from .views.focus_area_views import (
    focus_area_list, focus_area_create, focus_area_detail,
    focus_area_update, focus_area_delete
)
from .views.criteria_views import (
    criteria_list, criteria_create, criteria_detail,
    criteria_update, criteria_delete
)

urlpatterns = [

    # ------------------ Form -----------------------------------------------------

    # Form Type CRUD (serializer-based)
    path("form_types/", form_type_list, name="form_type_list"),
    path("form_types/create/", form_type_create, name="form_type_create"),
    path("form_types/<str:pk>/", form_type_detail, name="form_type_detail"),
    path("form_types/<str:pk>/update/", form_type_update, name="form_type_update"),
    path("form_types/<str:pk>/delete/", form_type_delete, name="form_type_delete"),

    # Data Type CRUD (serializer-based)
    path("data_types/", data_type_list, name="data_type_list"),
    path("data_types/create/", data_type_create, name="data_type_create"),
    path("data_types/<str:pk>/update/", data_type_update, name="data_type_update"),
    path("data_types/<str:pk>/delete/", data_type_delete, name="data_type_delete"),

    # Field Type CRUD (serializer-based)
    path("field_types/", field_type_list, name="field_type_list"),
    path("field_types/create/", field_type_create, name="field_type_create"),
    path("field_types/update/<str:pk>/", field_type_update, name="update_field_types"),
    path("field_types/delete/<str:pk>/", field_type_delete, name="field_type_delete"),

    # Form CRUD
    path("form/get/", get_dynamic_forms, name="get_dynamic_forms"),
    path("form/list/", get_dynamic_forms_list, name="get_dynamic_forms_list"),
    path("form/create/", form_create, name="form_create"),
    path("form/delete/<str:pk>/", delete_form, name="delete_forms"),
    path("form/by_type/", forms_by_type, name="forms_by_type"),
    path("form/with_sections/", form_with_sections_list, name="form_with_sections_list"),
    path("form/<str:pk>/", form_detail, name="form_detail"),
    path("form/fields/get/<str:form_id>/", get_form_fields, name="get_form_fields"),
    path("form/fields/create/<str:form_id>/", create_form_fields, name="create_form_fields"),

    # Form Draft
    path("form_draft/get/<str:form_id>/", get_form_draft, name="get_form_draft"),
    path("form_draft/save/<str:form_id>/", save_form_draft, name="save_form_draft"),

    # Bulk Upload
    path("form/bulk/template/download/", download_forms_template, name="download_forms_template"),
    path("form/bulk/upload/", bulk_upload_forms, name="bulk_upload_forms"),
    path("form/bulk/export/", export_forms_data, name="export_forms_data"),

    # Main Process CRUD
    path("main_processes/", main_process_list, name="main_process_list"),
    path("main_processes/create/", main_process_create, name="main_process_create"),
    path("main_processes/<str:pk>/", main_process_detail, name="main_process_detail"),
    path("main_processes/<str:pk>/update/", main_process_update, name="main_process_update"),
    path("main_processes/<str:pk>/delete/", main_process_delete, name="main_process_delete"),

    # Focus Area CRUD
    path("focus_areas/", focus_area_list, name="focus_area_list"),
    path("focus_areas/create/", focus_area_create, name="focus_area_create"),
    path("focus_areas/<str:pk>/", focus_area_detail, name="focus_area_detail"),
    path("focus_areas/<str:pk>/update/", focus_area_update, name="focus_area_update"),
    path("focus_areas/<str:pk>/delete/", focus_area_delete, name="focus_area_delete"),

    # Criteria CRUD
    path("criteria/", criteria_list, name="criteria_list"),
    path("criteria/create/", criteria_create, name="criteria_create"),
    path("criteria/<str:pk>/", criteria_detail, name="criteria_detail"),
    path("criteria/<str:pk>/update/", criteria_update, name="criteria_update"),
    path("criteria/<str:pk>/delete/", criteria_delete, name="criteria_delete"),

]
