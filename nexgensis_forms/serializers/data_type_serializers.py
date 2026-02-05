from rest_framework import serializers
from django.utils.timezone import localtime

from ..models import DataType


class DataTypeSerializer(serializers.ModelSerializer):
    """Serializer for DataType model - used for read operations"""
    type = serializers.CharField(source='name', read_only=True)
    created_on = serializers.SerializerMethodField()
    updated_on = serializers.SerializerMethodField()

    class Meta:
        model = DataType
        fields = ['id', 'type', 'name', 'validation_rules', 'created_on', 'updated_on']
        read_only_fields = ['id', 'created_on', 'updated_on']

    def get_created_on(self, obj):
        if obj.created_on:
            return localtime(obj.created_on).strftime('%Y-%m-%d %H:%M:%S')
        return None

    def get_updated_on(self, obj):
        if obj.updated_on:
            return localtime(obj.updated_on).strftime('%Y-%m-%d %H:%M:%S')
        return None


class DataTypeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for create/update operations"""
    name = serializers.CharField(
        max_length=50,
        required=True,
        help_text="Name of the data type"
    )
    validation_rules = serializers.JSONField(
        required=False,
        allow_null=True,
        help_text="Validation rules as JSON object"
    )

    class Meta:
        model = DataType
        fields = ['name', 'validation_rules']

    def validate_name(self, value):
        """Validate unique name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")

        value = value.strip()
        instance_id = self.instance.id if self.instance else None

        qs = DataType.objects.filter(name__iexact=value)
        if instance_id:
            qs = qs.exclude(id=instance_id)

        if qs.exists():
            raise serializers.ValidationError("Data type with this name already exists")
        return value

    def validate_validation_rules(self, value):
        """Validate validation_rules is a valid JSON object"""
        if value is not None and not isinstance(value, dict):
            raise serializers.ValidationError("Validation rules must be a valid JSON object")
        return value


class DataTypeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list view - matches original response format"""
    type = serializers.CharField(source='name', read_only=True)

    class Meta:
        model = DataType
        fields = ['id', 'type', 'validation_rules']
