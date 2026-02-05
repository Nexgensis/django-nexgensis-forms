from rest_framework import serializers
from django.utils.timezone import localtime

from ..models import FormType


class FormTypeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for form type list"""
    parent_form_type = serializers.CharField(source='parent_form_type.name', read_only=True, allow_null=True)

    # Add version tracking fields
    id = serializers.CharField(source='unique_code', read_only=True)
    version_id = serializers.UUIDField(source='id', read_only=True)

    class Meta:
        model = FormType
        fields = ['id', 'version_id', 'name', 'parent_form_type']


class FormTypeSerializer(serializers.ModelSerializer):
    """Full serializer for FormType model"""
    parent_form_type_id = serializers.UUIDField(source='parent_form_type.id', read_only=True, allow_null=True)
    parent_form_type_name = serializers.CharField(source='parent_form_type.name', read_only=True, allow_null=True)

    # TimestampedModel2 fields
    version_id = serializers.UUIDField(source='id', read_only=True)
    unique_code = serializers.CharField(read_only=True)
    created_by_name = serializers.SerializerMethodField()
    effective_end_date = serializers.SerializerMethodField()

    # Date formatters
    created_on = serializers.SerializerMethodField()
    updated_on = serializers.SerializerMethodField()

    class Meta:
        model = FormType
        fields = [
            'id', 'version_id', 'unique_code',  # Version tracking fields
            'name', 'description', 'parent_form_type_id',
            'parent_form_type_name', 'created_on', 'updated_on',
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


class FormTypeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for create/update operations"""
    name = serializers.CharField(
        max_length=100,
        required=True,
        help_text="Name of the form type"
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Description of the form type"
    )
    parent_form_type_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        write_only=True,
        help_text="ID of parent form type"
    )

    class Meta:
        model = FormType
        fields = ['name', 'description', 'parent_form_type_id']

    def validate_name(self, value):
        """Validate unique name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name is required")

        value = value.strip()
        if len(value) > 100:
            raise serializers.ValidationError("Name exceeds the maximum length of 100 characters")

        instance_id = self.instance.id if self.instance else None

        qs = FormType.objects.filter(name__iexact=value, effective_end_date__isnull=True)
        if instance_id:
            qs = qs.exclude(id=instance_id)

        if qs.exists():
            raise serializers.ValidationError("FormType with this name already exists")
        return value

    def validate_parent_form_type_id(self, value):
        """Validate parent form type exists"""
        if value:
            if not FormType.objects.filter(id=value, effective_end_date__isnull=True).exists():
                raise serializers.ValidationError("Parent FormType with the given ID does not exist")

            # Prevent circular reference
            if self.instance and value == self.instance.id:
                raise serializers.ValidationError("FormType cannot be its own parent")
        return value

    def create(self, validated_data):
        parent_id = validated_data.pop('parent_form_type_id', None)

        if parent_id:
            validated_data['parent_form_type'] = FormType.objects.get(id=parent_id, effective_end_date__isnull=True)

        return FormType.objects.create(**validated_data)

    def update(self, instance, validated_data):
        parent_id = validated_data.pop('parent_form_type_id', None)

        if parent_id is not None:
            if parent_id:
                instance.parent_form_type = FormType.objects.get(id=parent_id, effective_end_date__isnull=True)
            else:
                instance.parent_form_type = None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
