import uuid
from django.db import models
from django.conf import settings
from uuid_utils import uuid7
from django.utils import timezone


def uuid7_default():
    """Generate a UUID7 for use as a default value in model fields."""
    return uuid7()

# ------------------------------- Absatrct Models -------------------------------------
class TimestampedModel(models.Model):
    """
    Abstract base model with creation/update timestamps and soft delete.

    Provides:
    - created_on: Automatically set on creation
    - updated_on: Automatically updated on save
    - is_deleted: Soft delete flag
    """
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        """Soft delete: mark as deleted instead of removing from database."""
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_on'])

    def hard_delete(self, *args, **kwargs):
        """Permanently delete the record from database."""
        super().delete(*args, **kwargs)

    def restore(self, *args, **kwargs):
        """Restore a soft-deleted object."""
        self.is_deleted = False
        self.save(update_fields=['is_deleted', 'updated_on'])


class TimestampedModel2(models.Model):
    """
    Abstract base model with SCD Type 2 (Slowly Changing Dimension) versioning.

    Provides:
    - created_on: Automatically set on creation
    - created_by: User who created the record
    - effective_end_date: Soft delete via timestamp (None = active)
    - previous_version_id: Links to previous version for history tracking
    - unique_code: Auto-generated unique identifier

    Usage:
        class MyModel(TimestampedModel2):
            CODE_PREFIX = "MYMDL"  # Override to customize prefix
    """
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(class)s_created'
    )
    effective_end_date = models.DateTimeField(null=True, blank=True)
    previous_version_id = models.UUIDField(null=True, blank=True)
    unique_code = models.CharField(max_length=50, blank=True, editable=True)

    # Override this in child models to customize the prefix (e.g., "FRM", "FLD", "SEC")
    CODE_PREFIX = "NEX"

    class Meta:
        abstract = True
        # Note: Child models should add their own UniqueConstraint for unique_code
        # with condition=Q(effective_end_date__isnull=True) to allow versioning

    @property
    def is_current(self):
        """Check if this is the current/active version."""
        return self.effective_end_date is None

    def _generate_unique_code(self):
        """
        Generate a globally unique code like NEX-A1B2C3D4.
        Uses UUID4 for fully random, unique codes.
        """
        prefix = getattr(self, 'CODE_PREFIX', 'NEX')
        short_code = uuid.uuid4().hex[:8].upper()
        return f"{prefix}-{short_code}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate unique_code if not provided."""
        # Ensure id is set before generating unique_code
        if not self.id:
            self.id = uuid7()
        if not self.unique_code:
            self.unique_code = self._generate_unique_code()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Soft delete by setting effective_end_date."""
        self.effective_end_date = timezone.now()
        self.save(update_fields=['effective_end_date'])

    def hard_delete(self, *args, **kwargs):
        """Permanently delete the record."""
        super().delete(*args, **kwargs)

    def restore(self, *args, **kwargs):
        """Restore a soft-deleted object."""
        self.effective_end_date = None
        self.save(update_fields=['effective_end_date'])


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

    # Note: Location FK is project-specific. Add it in your consumer project:
    # location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True, blank=True)

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
