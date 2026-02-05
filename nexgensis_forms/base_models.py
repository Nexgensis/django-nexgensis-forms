"""
Base abstract models for Nexgensis Forms.

These models provide common functionality like timestamps, soft deletion,
and version tracking.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
from uuid_utils import uuid7


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
        'auth.User',
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


class TraceableModel(TimestampedModel):
    """
    Abstract model extending TimestampedModel with invalidation tracking.

    Useful for records that can be marked as invalid (e.g., voided transactions,
    cancelled forms) with audit trail of who invalidated and why.

    Provides:
    - All TimestampedModel fields (created_on, updated_on, is_deleted)
    - is_invalid: Flag to mark record as invalid
    - invalidated_at: When the record was invalidated
    - invalidated_by: Who invalidated the record
    - invalidated_reason: Why the record was invalidated
    """
    is_invalid = models.BooleanField(default=False)
    invalidated_at = models.DateTimeField(null=True, blank=True)
    invalidated_by = models.ForeignKey(
        'auth.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(class)s_invalidations'
    )
    invalidated_reason = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True

    def invalidate(self, invalidated_by=None, reason=None):
        """Mark this record as invalid."""
        self.is_invalid = True
        self.invalidated_at = timezone.now()
        self.invalidated_by = invalidated_by
        self.invalidated_reason = reason
        self.save(update_fields=[
            'is_invalid',
            'invalidated_at',
            'invalidated_by',
            'invalidated_reason',
            'updated_on'
        ])

    def revalidate(self):
        """Mark this record as valid again."""
        self.is_invalid = False
        self.invalidated_at = None
        self.invalidated_by = None
        self.invalidated_reason = None
        self.save(update_fields=[
            'is_invalid',
            'invalidated_at',
            'invalidated_by',
            'invalidated_reason',
            'updated_on'
        ])
