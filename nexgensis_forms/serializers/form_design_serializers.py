import uuid

from rest_framework import serializers
from django.utils.timezone import localtime
from django.db import transaction, models

from ..models import (
    FieldType, Form, FormType, FormDraft,
    FormSections, FormFields
)


# ============== Form Serializers ==============

class FormListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for form list"""
    type = serializers.CharField(source='form_type.name', read_only=True)
    created_on = serializers.SerializerMethodField()
    updated_on = serializers.SerializerMethodField()

    # Add minimal version tracking fields
    id = serializers.CharField(source='unique_code', read_only=True)
    version_id = serializers.UUIDField(source='id', read_only=True)

    class Meta:
        model = Form
        fields = [
            'id', 'version_id',  # Version IDs
            'title', 'type', 'description', 'is_completed',
            'version', 'parent_form', 'root_form',  # Keep existing version fields
            'created_on', 'updated_on'
        ]

    def get_created_on(self, obj):
        if obj.created_on:
            return localtime(obj.created_on).strftime('%Y-%m-%d %H:%M:%S')
        return None

    def get_updated_on(self, obj):
        # Backward compatibility - return None after migration
        if hasattr(obj, 'updated_on') and obj.updated_on:
            return localtime(obj.updated_on).strftime('%Y-%m-%d %H:%M:%S')
        return None


class FormSerializer(serializers.ModelSerializer):
    """Full serializer for Form model"""
    type = serializers.CharField(source='form_type.name', read_only=True)
    type_id = serializers.UUIDField(source='form_type.id', read_only=True)

    # TimestampedModel2 fields
    version_id = serializers.UUIDField(source='id', read_only=True)
    unique_code = serializers.CharField(read_only=True)
    created_by_name = serializers.SerializerMethodField()
    effective_end_date = serializers.SerializerMethodField()

    # Date formatters
    created_on = serializers.SerializerMethodField()
    updated_on = serializers.SerializerMethodField()

    class Meta:
        model = Form
        fields = [
            'id', 'version_id', 'unique_code',  # Version tracking fields
            'title', 'type', 'type_id', 'description', 'is_completed',
            'version', 'parent_form', 'root_form',  # Keep existing version fields
            'system_config', 'user_config',
            'created_on', 'updated_on',
            'created_by', 'created_by_name',  # Creator tracking
            'effective_end_date', 'previous_version_id'  # Version history
        ]
        read_only_fields = [
            'id', 'version_id', 'unique_code',
            'created_on', 'updated_on',
            'created_by', 'effective_end_date', 'previous_version_id'
        ]

    def get_created_on(self, obj):
        if obj.created_on:
            return localtime(obj.created_on).strftime('%Y-%m-%d %H:%M:%S')
        return None

    def get_updated_on(self, obj):
        # After migration, updated_on won't exist - return None for compatibility
        if hasattr(obj, 'updated_on') and obj.updated_on:
            return localtime(obj.updated_on).strftime('%Y-%m-%d %H:%M:%S')
        return None

    def get_created_by_name(self, obj):
        """Return creator's name"""
        if obj.created_by:
            name = f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
            return name or obj.created_by.username
        return None

    def get_effective_end_date(self, obj):
        """Format soft-delete timestamp"""
        if obj.effective_end_date:
            return localtime(obj.effective_end_date).strftime('%Y-%m-%d %H:%M:%S')
        return None


class FormCreateSerializer(serializers.Serializer):
    """Serializer for creating a new form"""
    title = serializers.CharField(max_length=255, required=True, help_text="Title of the form")
    type_id = serializers.CharField(required=True, help_text="ID or unique_code of the form type")
    desc = serializers.CharField(required=False, allow_blank=True, default="", help_text="Description")
    system_config = serializers.JSONField(required=False, default=dict, help_text="System configuration")
    user_config = serializers.JSONField(required=False, default=dict, help_text="User configuration")

    # Optional categorization foreign keys
    main_process = serializers.UUIDField(required=False, allow_null=True, help_text="UUID of the main process")
    criteria = serializers.UUIDField(required=False, allow_null=True, help_text="UUID of the criteria")
    location = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="unique_code or UUID of the location")

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Title is required")
        value = value.strip()
        if Form.objects.filter(title__iexact=value, effective_end_date__isnull=True).exists():
            raise serializers.ValidationError(f"A form with the title '{value}' already exists")
        return value

    def validate_type_id(self, value):
        """Validate form type exists - accepts both unique_code and UUID"""
        # Try lookup by unique_code first
        form_type = FormType.objects.filter(
            unique_code=value,
            effective_end_date__isnull=True
        ).first()

        # Fallback to UUID (only if value is a valid UUID)
        if not form_type:
            try:
                uuid.UUID(str(value))
                form_type = FormType.objects.filter(
                    id=value,
                    effective_end_date__isnull=True
                ).first()
            except (ValueError, AttributeError):
                pass  # Not a valid UUID, skip this lookup

        if not form_type:
            raise serializers.ValidationError("Form type does not exist")

        # Store the form_type object for use in create method
        self._form_type = form_type
        return value

    def validate_main_process(self, value):
        """Validate main process exists if provided"""
        if value:
            from ..models import MainProcess
            main_process = MainProcess.objects.filter(
                id=value,
                effective_end_date__isnull=True
            ).first()
            if not main_process:
                raise serializers.ValidationError("Main process does not exist")
            self._main_process = main_process
        return value

    def validate_criteria(self, value):
        """Validate criteria exists if provided"""
        if value:
            from ..models import Criteria
            criteria = Criteria.objects.filter(
                id=value,
                effective_end_date__isnull=True
            ).first()
            if not criteria:
                raise serializers.ValidationError("Criteria does not exist")
            self._criteria = criteria
        return value

    def validate_location(self, value):
        """Validate location exists if provided - accepts both unique_code and UUID"""
        if value:
            try:
                from configapp.models import Location
            except ImportError:
                Location = None  # Optional - configure via NEXGENSIS_FORMS settings
            # Try lookup by unique_code first
            location = Location.objects.filter(
                unique_code=value,
                effective_end_date__isnull=True
            ).first()

            # Fallback to UUID (only if value is a valid UUID)
            if not location:
                try:
                    uuid.UUID(str(value))
                    location = Location.objects.filter(
                        id=value,
                        effective_end_date__isnull=True
                    ).first()
                except (ValueError, AttributeError):
                    pass  # Not a valid UUID, skip this lookup

            if not location:
                raise serializers.ValidationError("Location does not exist")
            self._location = location
        return value

    @transaction.atomic
    def create(self, validated_data):
        # Use the validated form_type object stored during validation
        form_type = self._form_type
        form = Form.objects.create(
            title=validated_data['title'],
            form_type=form_type,
            description=validated_data.get('desc', ''),
            version=1,
            is_completed=False,
            system_config=validated_data.get('system_config', {}),
            user_config=validated_data.get('user_config', {}),
            main_process=getattr(self, '_main_process', None),
            criteria=getattr(self, '_criteria', None),
            location=getattr(self, '_location', None)
        )
        # Set root_form to itself
        form.root_form = form
        form.save(update_fields=['root_form'])
        return form


# ============== FormDraft Serializers ==============

class FormDraftSerializer(serializers.ModelSerializer):
    """Serializer for FormDraft model"""
    form_details = serializers.SerializerMethodField()

    class Meta:
        model = FormDraft
        fields = ['id', 'form', 'draft_data', 'form_details']
        read_only_fields = ['id']

    def get_form_details(self, obj):
        form = obj.form
        return {
            'title': form.title,
            'form_type': form.form_type.name if form.form_type else None,
            'description': form.description,
            'version': form.version,
            'created_on': localtime(form.created_on).strftime('%Y-%m-%d %H:%M:%S') if form.created_on else None,
        }


class FormDraftCreateUpdateSerializer(serializers.Serializer):
    """Serializer for create/update form draft"""
    draft_data = serializers.JSONField(required=True, help_text="Draft JSON data")

    def validate_draft_data(self, value):
        if not value:
            raise serializers.ValidationError("Draft data is required")
        return value


# ============== FormFields Serializers ==============

class FormFieldSerializer(serializers.Serializer):
    """Serializer for individual form field"""
    label = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    type_id = serializers.UUIDField(required=True)
    required = serializers.BooleanField(required=False, default=False)
    fields = serializers.ListField(child=serializers.DictField(), required=False, default=list)

    def validate_type_id(self, value):
        if not FieldType.objects.filter(id=value).exists():
            raise serializers.ValidationError("Field type not found")
        return value


class FormSectionSerializer(serializers.Serializer):
    """Serializer for form section"""
    section_name = serializers.CharField(required=True)
    fields = FormFieldSerializer(many=True, required=False, default=list)

    def validate_section_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Section name is required")
        return value.strip()


class FormFieldsCreateSerializer(serializers.Serializer):
    """Serializer for creating form fields"""
    sections = FormSectionSerializer(many=True, required=True)
    system_config = serializers.JSONField(required=False, default=dict)
    user_config = serializers.JSONField(required=False, default=dict)


# ============== FormSections Response Serializer ==============

class FormWithSectionsSerializer(serializers.ModelSerializer):
    """Serializer for form with sections"""
    sections = serializers.SerializerMethodField()
    name = serializers.CharField(source='title', read_only=True)

    class Meta:
        model = Form
        fields = ['id', 'name', 'sections']

    def get_sections(self, obj):
        sections = FormSections.objects.filter(form=obj).order_by('id')
        return [
            {
                'section_id': section.id,
                'section_name': section.name
            }
            for section in sections
        ]


# ============== Dynamic Form Response Serializer ==============

class DynamicFormResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for dynamic form list response.
    Used in get_dynamic_forms API for consistent field mapping.
    """
    name = serializers.CharField(source='title', read_only=True)
    type = serializers.CharField(source='form_type.name', read_only=True, allow_null=True)
    all_versions = serializers.SerializerMethodField()
    created_on = serializers.SerializerMethodField()
    updated_on = serializers.SerializerMethodField()

    # Categorization foreign keys
    main_process = serializers.SerializerMethodField()
    criteria = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    # Version tracking fields
    id = serializers.CharField(source='unique_code', read_only=True)
    version_id = serializers.UUIDField(source='id', read_only=True)

    class Meta:
        model = Form
        fields = [
            'id', 'version_id',  # Version IDs
            'name', 'title', 'type', 'description', 'is_completed',
            'version', 'all_versions',
            'main_process', 'criteria', 'location',
            'created_on', 'updated_on'
        ]

    def get_all_versions(self, obj):
        """Get all versions of this form grouped by root"""
        # Skip all_versions if is_completed=false in context
        if not self.context.get('include_all_versions', True):
            return None

        root_id = obj.root_form_id or obj.id
        return list(
            Form.objects.filter(
                models.Q(root_form_id=root_id) | models.Q(id=root_id),
                effective_end_date__isnull=True  # Changed from is_deleted=False
            ).values('id', 'version', 'unique_code').order_by('version')  # Added unique_code
        )

    def to_representation(self, instance):
        """Override to conditionally exclude all_versions from response"""
        data = super().to_representation(instance)
        # Remove all_versions if it's None (when is_completed=false)
        if data.get('all_versions') is None:
            del data['all_versions']
        return data

    def get_created_on(self, obj):
        if obj.created_on:
            return localtime(obj.created_on).strftime('%Y-%m-%d %H:%M:%S')
        return None

    def get_updated_on(self, obj):
        # Backward compatibility - return None after migration
        if hasattr(obj, 'updated_on') and obj.updated_on:
            return localtime(obj.updated_on).strftime('%Y-%m-%d %H:%M:%S')
        return None

    def get_main_process(self, obj):
        if obj.main_process:
            return {
                'id': str(obj.main_process.id),
                'name': obj.main_process.name
            }
        return None

    def get_criteria(self, obj):
        if obj.criteria:
            return {
                'id': str(obj.criteria.id),
                'name': obj.criteria.name
            }
        return None

    def get_location(self, obj):
        if obj.location:
            return {
                'id': str(obj.location.id),
                'name': obj.location.location_name
            }
        return None


# ============== Form Fields Response Serializers ==============

class FormFieldResponseSerializer(serializers.Serializer):
    """
    Serializer for individual form field response.
    Handles recursive sub_fields and dynamic additional_info spreading.
    """
    field_id = serializers.UUIDField(source='id')
    label = serializers.CharField()
    name = serializers.CharField()
    type_id = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    required = serializers.BooleanField()
    end_point = serializers.SerializerMethodField()
    fields = serializers.SerializerMethodField()

    def get_type_id(self, obj):
        if obj.field_type and obj.field_type.data_type:
            return obj.field_type.data_type.id
        return None

    def get_type(self, obj):
        if obj.field_type and obj.field_type.data_type:
            return obj.field_type.data_type.name
        return None

    def get_end_point(self, obj):
        if obj.field_type:
            return obj.field_type.endpoint
        return None

    def get_fields(self, obj):
        """Handle recursive sub_fields"""
        sub_fields = obj.sub_fields.all()
        if sub_fields.exists():
            return FormFieldResponseSerializer(sub_fields, many=True).data
        return None

    def to_representation(self, instance):
        """Override to dynamically add additional_info fields"""
        data = super().to_representation(instance)

        # Remove 'fields' key if None (no sub_fields)
        if data.get('fields') is None:
            del data['fields']

        # Dynamically spread additional_info fields (excluding 'end_point')
        if instance.additional_info:
            for key, value in instance.additional_info.items():
                if key != 'end_point':
                    data[key] = value

        return data


class FormSectionResponseSerializer(serializers.Serializer):
    """Serializer for form section with fields"""
    section_id = serializers.UUIDField(source='id')
    section_name = serializers.CharField(source='name')
    fields = serializers.SerializerMethodField()

    def get_fields(self, obj):
        """Get top-level fields for this section"""
        top_level_fields = FormFields.objects.filter(
            section=obj,
            parent_field__isnull=True
        ).order_by('order')
        return FormFieldResponseSerializer(top_level_fields, many=True).data


class FormDetailsResponseSerializer(serializers.Serializer):
    """Serializer for form details in get_form_fields response"""
    title = serializers.CharField()
    form_type = serializers.SerializerMethodField()
    description = serializers.CharField()
    version = serializers.IntegerField()
    created_on = serializers.DateTimeField()
    workflow_name = serializers.SerializerMethodField()

    def get_form_type(self, obj):
        if obj.form_type:
            return obj.form_type.name
        return None

    def get_workflow_name(self, obj):
        """Get workflow name from context"""
        return self.context.get('workflow_name')
