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
    'USER_MODEL': 'auth.User',  # Model for created_by field
    'LOCATION_MODEL': None,  # Optional: 'yourapp.Location'
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
| `USER_MODEL` | `'auth.User'` | User model for created_by fields |
| `LOCATION_MODEL` | `None` | Optional location model |
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
