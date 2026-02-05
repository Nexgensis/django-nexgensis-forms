from django.db import models
from uuid_utils import uuid7
from .base_models import TimestampedModel, TimestampedModel2
from .utils import format_date

def uuid7_default():
    """Generate a UUID7 for use as a default value in model fields."""
    return uuid7()

# ------------------------------- Form Models -------------------------------------
class FormType(TimestampedModel2):
    CODE_PREFIX = "FTYPE"

    id = models.UUIDField(primary_key=True, default=uuid7_default, editable=False)
    name = models.CharField(max_length=100)
    description=models.TextField(null=True, blank=True)
    parent_form_type = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name="sub_forms")

    # TimestampedModel2 provides: created_on, created_by, effective_end_date, previous_version_id, unique_code

    @property
    def is_deleted(self):
        """Backward compatibility: map effective_end_date to is_deleted"""
        return self.effective_end_date is not None

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['unique_code'],
                condition=models.Q(effective_end_date__isnull=True),
                name='unique_active_formtype_code'
            )
        ]

    def __str__(self):
        return self.name

class DataType(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid7_default, editable=False)
    name = models.CharField(max_length=50, unique=True)
    validation_rules = models.JSONField(null=True, blank=True, help_text="Validation rules for the data type")
    def __str__(self):
        return self.name

class FieldType(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid7_default, editable=False)
    name = models.CharField(max_length=50, unique=True)
    data_type = models.ForeignKey(DataType, on_delete=models.PROTECT, related_name='field_types')
    dynamic = models.BooleanField(default=False, help_text="Is this field type dynamic?")
    endpoint = models.CharField(max_length=255, null=True, blank=True, help_text="API endpoint for dynamic field types")
    validation_rules = models.JSONField(null=True, blank=True, help_text="Validation rules for the field type")
    default = models.BooleanField(default=False, help_text="Is this field type the default for its data type?")


class Form(TimestampedModel2):
    CODE_PREFIX = "FORM"

    id = models.UUIDField(primary_key=True, default=uuid7_default, editable=False)
    title = models.CharField(max_length=255)
    form_type = models.ForeignKey(FormType, on_delete=models.CASCADE)
    description=models.TextField(null=True, blank=True)

    # Optional categorization foreign keys
    main_process = models.ForeignKey('MainProcess', on_delete=models.SET_NULL, null=True, blank=True, related_name='forms')
    criteria = models.ForeignKey('Criteria', on_delete=models.SET_NULL, null=True, blank=True, related_name='forms')

    # Location field - stores location ID as string (optional)
    # Users can configure NEXGENSIS_FORMS['LOCATION_MODEL'] to link to their location model
    location_id = models.CharField(max_length=255, null=True, blank=True, help_text="Location identifier (optional)")

    is_completed = models.BooleanField(default=False, help_text="Is the form completed?")

    # Keep existing version tracking fields for backward compatibility
    parent_form = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name="sub_forms")
    root_form = models.ForeignKey("self", null=True, blank=True, related_name="versions", on_delete=models.SET_NULL)
    version = models.PositiveIntegerField(default=1)

    system_config = models.JSONField(default=dict, blank=True)  # No-code backend settings
    user_config = models.JSONField(default=dict, blank=True)  # Low-code frontend customization

    # TimestampedModel2 provides: created_on, created_by, effective_end_date, previous_version_id, unique_code

    @property
    def is_deleted(self):
        """Backward compatibility: map effective_end_date to is_deleted"""
        return self.effective_end_date is not None

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['unique_code'],
                condition=models.Q(effective_end_date__isnull=True),
                name='unique_active_form_code'
            )
        ]

    def __str__(self):
        return self.title

class FormDraft(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid7_default, editable=False)
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    draft_data = models.JSONField(null=True, blank=True, help_text="Draft data for the form")

    def __str__(self):
        return f"Draft for {self.form.title}"


class FormSections(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid7_default, editable=False)
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description=models.TextField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Order of the section in the form")
    dependency = models.JSONField(null=True, blank=True, help_text="Section dependency configuration")
    class Meta:
        unique_together = ('form', 'name')

class FormFields(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid7_default, editable=False)
    label = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    field_type = models.ForeignKey(FieldType, on_delete=models.PROTECT)
    section = models.ForeignKey(FormSections, on_delete=models.CASCADE)
    required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0, help_text="Order of the fields in the form")
    additional_info = models.JSONField(null=True, blank=True, help_text="Additional values for the data type")
    parent_field = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name="sub_fields")
    dependency = models.JSONField(null=True, blank=True, help_text="Field dependency configuration")
    class Meta:
        unique_together = ('label', 'section', 'parent_field')


# ------------------------------- Categorization Models (Optional) -------------------------------------
# These models provide optional categorization for forms.
# They can be disabled via NEXGENSIS_FORMS['ENABLE_CATEGORIZATION'] = False

class MainProcess(TimestampedModel2):
    CODE_PREFIX = "MPROC"
    id = models.UUIDField(primary_key=True, default=uuid7_default, editable=False)
    name = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['unique_code'],
                condition=models.Q(effective_end_date__isnull=True),
                name='unique_active_mainprocess_code'
            )
        ]

    def __str__(self):
        return self.name

class FocusArea(TimestampedModel2):
    CODE_PREFIX = "FAREA"
    id = models.UUIDField(primary_key=True, default=uuid7_default, editable=False)
    name = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['unique_code'],
                condition=models.Q(effective_end_date__isnull=True),
                name='unique_active_focusarea_code'
            )
        ]

    def __str__(self):
        return self.name

class Criteria(TimestampedModel2):
    CODE_PREFIX = "CRIT"
    id = models.UUIDField(primary_key=True, default=uuid7_default, editable=False)
    name = models.CharField(max_length=255)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['unique_code'],
                condition=models.Q(effective_end_date__isnull=True),
                name='unique_active_criteria_code'
            )
        ]

    def __str__(self):
        return self.name
