# Django Nexgensis Forms

A powerful Django app for creating and managing dynamic forms with versioning, hierarchical structures, and flexible field types.

## Features

- ✨ **Dynamic Form Builder**: Create forms programmatically with flexible field types
- 📊 **Hierarchical Forms**: Support for parent-child form type relationships
- 🔄 **Version Control**: Built-in SCD Type 2 versioning for forms and form types
- 📝 **Flexible Fields**: Nested form fields with parent-child relationships
- 📤 **Bulk Operations**: Excel import/export with validation
- 🔒 **Soft Delete**: Non-destructive deletion with effective date tracking
- 🎯 **Dynamic Field Types**: Extensible field types with validation rules
- 🏷️ **Categorization**: Optional categorization with MainProcess, Criteria, FocusArea
- 💾 **Draft System**: Save forms as drafts before finalizing
- 🔗 **Workflow Integration**: Optional integration with django-nexgensis-workflow

## Installation

```bash
pip install django-nexgensis-forms
```

## Quick Start

### 1. Add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'drf_yasg',
    'nexgensis_forms',
]
```

### 2. Configure Settings (Optional)

```python
NEXGENSIS_FORMS = {
    'WORKFLOW_INTEGRATION': False,  # Enable if using nexgensis-workflow
    'ENABLE_BULK_UPLOAD': True,
    'MAX_UPLOAD_SIZE': 10 * 1024 * 1024,  # 10MB
}
```

### 3. Run Migrations

```bash
python manage.py migrate nexgensis_forms
```

### 4. Include URLs

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    ...
    path('api/forms/', include('nexgensis_forms.urls')),
]
```

## Usage Examples

### Creating a Form Type

```python
from nexgensis_forms.models import FormType

form_type = FormType.objects.create(
    name="Customer Feedback",
    description="Customer satisfaction survey"
)
```

### Creating a Form with Sections and Fields

```python
from nexgensis_forms.models import Form, FormSections, FormFields, FieldType, DataType

# Create form
form = Form.objects.create(
    title="Q1 2024 Customer Survey",
    form_type=form_type,
    description="Quarterly customer feedback form"
)

# Create section
section = FormSections.objects.create(
    form=form,
    name="Customer Information",
    order=1
)

# Get or create field type
text_data_type = DataType.objects.get(name="text")
text_field_type = FieldType.objects.get(
    name="Short Text",
    data_type=text_data_type
)

# Create field
field = FormFields.objects.create(
    section=section,
    label="Customer Name",
    name="customer_name",
    field_type=text_field_type,
    required=True,
    order=1
)
```

### API Usage

#### Get All Forms

```bash
GET /api/forms/form/get/
```

#### Create Form via API

```bash
POST /api/forms/form/create/
Content-Type: application/json

{
    "title": "Employee Onboarding",
    "form_type": "uuid-of-form-type",
    "description": "New employee onboarding checklist"
}
```

#### Bulk Upload from Excel

```bash
# Download template
GET /api/forms/form/bulk/template/download/

# Upload filled template
POST /api/forms/form/bulk/upload/
Content-Type: multipart/form-data

file: <excel-file>
```

## API Endpoints

### Form Types
- `GET /form_types/` - List form types
- `POST /form_types/create/` - Create form type
- `PUT /form_types/<pk>/update/` - Update form type
- `DELETE /form_types/<pk>/delete/` - Delete form type

### Forms
- `GET /form/get/` - List forms with filters
- `POST /form/create/` - Create form
- `GET /form/<pk>/` - Get form detail
- `DELETE /form/delete/<pk>/` - Delete form
- `POST /form/fields/create/<form_id>/` - Add fields to form

### Bulk Operations
- `GET /form/bulk/template/download/` - Download Excel template
- `POST /form/bulk/upload/` - Bulk upload forms
- `GET /form/bulk/export/` - Export forms to Excel

### Data Types & Field Types
- `GET /data_types/` - List data types
- `POST /data_types/create/` - Create data type
- `GET /field_types/` - List field types
- `POST /field_types/create/` - Create field type

## Models

### Core Models

- **FormType**: Categorization of forms with hierarchical support
- **Form**: Main form entity with versioning
- **FormSections**: Sections within a form
- **FormFields**: Individual fields with nested support
- **DataType**: Base data types (text, number, date, etc.)
- **FieldType**: Reusable field type definitions
- **FormDraft**: Draft storage for forms in progress

### Categorization Models

- **MainProcess**: Process categorization
- **FocusArea**: Focus area categorization
- **Criteria**: Criteria categorization

## Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `WORKFLOW_CHECKLIST_MODEL` | `None` | Swappable workflow checklist model |
| `WORKFLOW_INTEGRATION` | `False` | Enable workflow integration |
| `ENABLE_BULK_UPLOAD` | `True` | Enable Excel bulk operations |
| `MAX_UPLOAD_SIZE` | `10MB` | Maximum Excel file size |
| `ALLOWED_FILE_TYPES` | `['xlsx', 'xls']` | Allowed file extensions |

## Advanced Features

### Version Control

Forms and form types use SCD Type 2 versioning:

```python
# Create new version
old_form = Form.objects.get(pk=form_id)
new_form = Form.objects.create(
    title=old_form.title,
    form_type=old_form.form_type,
    parent_form=old_form,
    root_form=old_form.root_form or old_form,
    version=old_form.version + 1
)

# Soft delete old version
old_form.delete()  # Sets effective_end_date
```

### Dynamic Field Types

Create field types with dynamic endpoints:

```python
field_type = FieldType.objects.create(
    name="Department Selector",
    data_type=dropdown_type,
    dynamic=True,
    endpoint="/api/departments/list/",
    validation_rules={"min_selections": 1}
)
```

### Nested Fields

Create sub-fields under parent fields:

```python
parent_field = FormFields.objects.create(
    section=section,
    label="Address",
    name="address",
    field_type=group_field_type,
    order=1
)

child_field = FormFields.objects.create(
    section=section,
    label="Street",
    name="street",
    field_type=text_field_type,
    parent_field=parent_field,
    order=1
)
```

## Extending Forms with Project-Specific Fields

The package provides a generic Form model without project-specific fields like `location`. Follow these 4 steps to add full location support in your consumer project.

### Step 1: Extend the Model

```python
# yourproject/models.py
from django.db import models
from nexgensis_forms.models import Form

class ProjectForm(Form):
    """Extended Form with location support."""
    location = models.ForeignKey(
        'configapp.Location',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='forms'
    )
```

Then generate migrations:

```bash
python manage.py makemigrations yourproject
python manage.py migrate
```

### Step 2: Extend Serializers

Override only the serializers that need the new field:

```python
# yourproject/serializers.py
from rest_framework import serializers
from nexgensis_forms.serializers import FormCreateSerializer, FormSerializer, FormListSerializer
from configapp.models import Location
from .models import ProjectForm

# 1. Create - accept location in request
class ProjectFormCreateSerializer(FormCreateSerializer):
    location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), required=False, allow_null=True
    )

# 2. Detail - return location in response
class ProjectFormSerializer(FormSerializer):
    location = serializers.SerializerMethodField()

    class Meta(FormSerializer.Meta):
        model = ProjectForm
        fields = FormSerializer.Meta.fields + ['location']

    def get_location(self, obj):
        if obj.location:
            return {"id": str(obj.location.id), "name": obj.location.name}
        return None

# 3. List - return location in list response
class ProjectFormListSerializer(FormListSerializer):
    location = serializers.SerializerMethodField()

    class Meta(FormListSerializer.Meta):
        model = ProjectForm
        fields = FormListSerializer.Meta.fields + ['location']

    def get_location(self, obj):
        if obj.location:
            return {"id": str(obj.location.id), "name": obj.location.name}
        return None
```

### Step 3: Override Views

Only 4 form views need overriding. All other endpoints (DataType, FieldType, FormType, MainProcess, FocusArea, Criteria, FormDraft, BulkUpload, FormFields) work directly from the package.

```python
# yourproject/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from nexgensis_forms.utils import api_response
from .models import ProjectForm
from .serializers import ProjectFormCreateSerializer, ProjectFormSerializer, ProjectFormListSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_forms(request):
    """List forms with location filter support."""
    forms = ProjectForm.objects.select_related(
        'form_type', 'main_process', 'criteria', 'location'
    ).filter(effective_end_date__isnull=True)

    # Location filter
    location_id = request.query_params.get('location')
    if location_id:
        forms = forms.filter(location_id=location_id)

    # Add other filters as needed (form_type, main_process, criteria, search)
    # ... your filter logic here

    serializer = ProjectFormListSerializer(forms, many=True)
    return api_response(data=serializer.data, message="Forms retrieved")

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_form(request):
    """Create form with location support."""
    serializer = ProjectFormCreateSerializer(data=request.data)
    if serializer.is_valid():
        form = serializer.save()
        # Set location if provided
        location = serializer.validated_data.get('location')
        if location:
            form.location = location
            form.save(update_fields=['location'])
        return api_response(data={"id": str(form.id)}, message="Form created", status_code=201)
    return api_response(errors=serializer.errors, message="Validation failed", status_code=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def form_detail(request, pk):
    """Get form detail with location."""
    try:
        form = ProjectForm.objects.select_related(
            'form_type', 'main_process', 'criteria', 'location'
        ).get(pk=pk)
        serializer = ProjectFormSerializer(form)
        return api_response(data=serializer.data, message="Form retrieved")
    except ProjectForm.DoesNotExist:
        return api_response(message="Form not found", status_code=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_forms_list(request):
    """List forms (simple) with location filter."""
    forms = ProjectForm.objects.select_related(
        'form_type', 'location'
    ).filter(effective_end_date__isnull=True)

    location_id = request.query_params.get('location')
    if location_id:
        forms = forms.filter(location_id=location_id)

    serializer = ProjectFormListSerializer(forms, many=True)
    return api_response(data=serializer.data, message="Forms retrieved")
```

### Step 4: Override URLs

Place your custom URLs **before** the package include so they take priority:

```python
# yourproject/urls.py
from django.urls import path, include
from . import views

urlpatterns = [
    # Your overridden form endpoints (with location support)
    path('api/forms/form/get/', views.get_forms, name='get_forms'),
    path('api/forms/form/list/', views.get_forms_list, name='get_forms_list'),
    path('api/forms/form/create/', views.create_form, name='create_form'),
    path('api/forms/form/<str:pk>/', views.form_detail, name='form_detail'),

    # Package handles remaining ~37 endpoints automatically
    path('api/forms/', include('nexgensis_forms.urls')),
]
```

### Available Serializers for Extension

| Serializer | Purpose | Extend when adding fields to |
|------------|---------|------------------------------|
| `FormCreateSerializer` | Form creation | Create API |
| `FormSerializer` | Form detail response | Detail API |
| `FormListSerializer` | Form list response | List API |
| `FormWithSectionsSerializer` | Form with sections | Sections API |
| `FormDraftSerializer` | Draft response | Draft API |

### Available Views for Override

| View Function | URL Pattern | Override when |
|--------------|-------------|---------------|
| `get_dynamic_forms` | `form/get/` | Adding list filters |
| `get_dynamic_forms_list` | `form/list/` | Adding list filters |
| `form_create` | `form/create/` | Adding fields to creation |
| `form_detail` | `form/<pk>/` | Adding fields to response |
| `forms_by_type` | `form/by_type/` | Adding filters |
| `form_with_sections_list` | `form/with_sections/` | Adding fields to sections response |

Views that do NOT need overriding: DataType, FieldType, FormType, MainProcess, FocusArea, Criteria, FormDraft, FormFields, BulkUpload.

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Code Quality

```bash
black nexgensis_forms/
flake8 nexgensis_forms/
isort nexgensis_forms/
```

## Requirements

- Python >= 3.10
- Django >= 4.2
- djangorestframework >= 3.14
- drf-yasg >= 1.21
- openpyxl >= 3.1
- pytz >= 2023.3
- uuid-utils >= 0.6

## License

MIT License - see LICENSE file for details

## Support

- Documentation: [GitHub Wiki](https://github.com/nexgensis/django-nexgensis-forms/wiki)
- Issue Tracker: [GitHub Issues](https://github.com/nexgensis/django-nexgensis-forms/issues)
- Source Code: [GitHub](https://github.com/nexgensis/django-nexgensis-forms)

## Related Packages

- [django-nexgensis-workflow](https://pypi.org/project/django-nexgensis-workflow/) - Workflow engine for multi-stage processes

## Changelog

### Version 1.0.0 (2024)

- Initial release
- Dynamic form builder
- Version control support
- Bulk Excel operations
- Hierarchical forms and fields
- Soft delete with effective dating
- REST API with Swagger documentation
