"""Django admin configuration for Nexgensis Forms."""

from django.contrib import admin
from .models import (
    FormType,
    DataType,
    FieldType,
    Form,
    FormDraft,
    FormSections,
    FormFields,
    MainProcess,
    FocusArea,
    Criteria,
)

# Core Form Models
admin.site.register(FormType)
admin.site.register(DataType)
admin.site.register(FieldType)
admin.site.register(Form)
admin.site.register(FormDraft)
admin.site.register(FormSections)
admin.site.register(FormFields)

# Categorization Models (Optional)
admin.site.register(MainProcess)
admin.site.register(FocusArea)
admin.site.register(Criteria)
