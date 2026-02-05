# Changelog - django-nexgensis-forms

## Version 1.0.0 (2024) - Initial Release

### ✅ Added
- Dynamic form builder with 7 core models
- Hierarchical form types with versioning (SCD Type 2)
- Flexible field types with dynamic endpoints
- Nested form fields with parent-child relationships
- Section-based form organization
- Draft system for work-in-progress forms
- Bulk Excel import/export with validation
- 3 optional categorization models (MainProcess, FocusArea, Criteria)
- 41 REST API endpoints with Swagger documentation
- Soft delete with effective date tracking
- Configuration layer for customization
- Complete serializers for all models
- Comprehensive validation

### 🧹 Removed (Legacy Models)
- Removed `Section` model (duplicate of FormSections)
- Removed `Parameter` model (legacy, unused)
- Removed `ParameterData` model (legacy, unused)
- Removed `ChecklistForm` model (workflow-specific)

### 🔧 Fixed
- Removed broken djangoapp import from urls.py
- Abstracted Location FK to use string reference
- Fixed all imports to use relative paths
- Cleaned up admin registrations

### 📊 Final Package Stats
- **10 Models**: 7 core + 3 optional categorization
- **41 API Endpoints**: All generic and reusable
- **43 Python Files**: Clean, well-organized
- **0 External Dependencies**: Self-contained (except Django/DRF)

### 📝 Models Breakdown

#### Core Models (7)
1. `FormType` - Form categorization with hierarchy
2. `DataType` - Field data types (text, number, date, etc.)
3. `FieldType` - Reusable field type definitions
4. `Form` - Main form entity with versioning
5. `FormDraft` - Draft storage
6. `FormSections` - Form sections/groups
7. `FormFields` - Individual fields with nesting support

#### Optional Categorization Models (3)
8. `MainProcess` - Process categorization
9. `FocusArea` - Focus area tags
10. `Criteria` - Criteria tags

### 🎯 API Endpoints

**Form Type Management** (5 endpoints)
- List, Create, Detail, Update, Delete

**Data Type Management** (4 endpoints)
- List, Create, Update, Delete

**Field Type Management** (4 endpoints)
- List, Create, Update, Delete

**Form Management** (8 endpoints)
- Get (with filters), List, Create, Detail, Delete
- By Type, With Sections, Fields CRUD

**Form Draft** (2 endpoints)
- Get Draft, Save Draft

**Bulk Operations** (3 endpoints)
- Download Template, Upload, Export

**Categorization** (15 endpoints)
- MainProcess: List, Create, Detail, Update, Delete (5)
- FocusArea: List, Create, Detail, Update, Delete (5)
- Criteria: List, Create, Detail, Update, Delete (5)

### 🔌 Integration

**Works With:**
- Django 4.2+
- Django REST Framework 3.14+
- Any Django project needing dynamic forms

**Optional Integration:**
- django-nexgensis-workflow (for workflow integration)

### 📦 Installation

```bash
pip install django-nexgensis-forms
```

Add to settings:
```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'drf_yasg',
    'nexgensis_forms',
]
```

Include URLs:
```python
path('api/forms/', include('nexgensis_forms.urls')),
```

### ⚙️ Configuration (Optional)

```python
NEXGENSIS_FORMS = {
    'USER_MODEL': 'auth.User',
    'LOCATION_MODEL': None,  # Optional: 'yourapp.Location'
    'WORKFLOW_INTEGRATION': False,
    'ENABLE_BULK_UPLOAD': True,
    'MAX_UPLOAD_SIZE': 10 * 1024 * 1024,  # 10MB
}
```

### 🚀 What Makes It Dynamic

1. **Flexible Field Types**: Create any field type with custom validation
2. **Dynamic Endpoints**: Field types can fetch options from API endpoints
3. **Nested Fields**: Unlimited field nesting with parent-child relationships
4. **Version Control**: Full history tracking with SCD Type 2
5. **Conditional Fields**: Dependency-based field display
6. **JSON Configuration**: system_config and user_config for flexibility
7. **Hierarchical Forms**: Form types can have parent-child relationships

### 📄 License

MIT License - Free for commercial and personal use

### 🔗 Links

- GitHub: https://github.com/nexgensis/django-nexgensis-forms
- PyPI: https://pypi.org/project/django-nexgensis-forms/
- Documentation: https://github.com/nexgensis/django-nexgensis-forms/wiki

---

## Upgrade Notes

### From formsapp to nexgensis_forms

If migrating from the original formsapp:

1. **Models Removed:**
   - `Section` → Use `FormSections` instead
   - `Parameter`, `ParameterData` → No longer supported
   - `ChecklistForm` → Use Form directly with workflow

2. **No API Changes:**
   - All URLs remain the same
   - All endpoints work identically
   - Frontend code requires no changes

3. **Configuration:**
   - Add `NEXGENSIS_FORMS` settings
   - Configure optional models if needed

4. **Migration Path:**
   - Keep using formsapp in production
   - Use nexgensis_forms for new projects
   - Migrate data when ready
