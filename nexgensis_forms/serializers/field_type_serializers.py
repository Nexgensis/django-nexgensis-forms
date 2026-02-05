from rest_framework import serializers
from django.utils.timezone import localtime

from ..models import FieldType, DataType


# ============== FieldType Serializers ==============

class FieldTypeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for field type list"""
    label = serializers.CharField(source='name', read_only=True)
    type_id = serializers.UUIDField(source='data_type.id', read_only=True)
    type = serializers.CharField(source='data_type.name', read_only=True)
    end_point = serializers.CharField(source='endpoint', read_only=True)

    class Meta:
        model = FieldType
        fields = ['id', 'label', 'type_id', 'type', 'dynamic', 'end_point', 'validation_rules', 'default']


class FieldTypeSerializer(serializers.ModelSerializer):
    """Full serializer for FieldType model"""
    label = serializers.CharField(source='name', read_only=True)
    type_id = serializers.UUIDField(source='data_type.id', read_only=True)
    type = serializers.CharField(source='data_type.name', read_only=True)
    end_point = serializers.CharField(source='endpoint', read_only=True)
    created_on = serializers.SerializerMethodField()
    updated_on = serializers.SerializerMethodField()

    class Meta:
        model = FieldType
        fields = [
            'id', 'label', 'name', 'type_id', 'type', 'dynamic',
            'end_point', 'validation_rules', 'default', 'created_on', 'updated_on'
        ]
        read_only_fields = ['id', 'created_on', 'updated_on']

    def get_created_on(self, obj):
        if obj.created_on:
            return localtime(obj.created_on).strftime('%Y-%m-%d %H:%M:%S')
        return None

    def get_updated_on(self, obj):
        if obj.updated_on:
            return localtime(obj.updated_on).strftime('%Y-%m-%d %H:%M:%S')
        return None


class FieldTypeCreateUpdateSerializer(serializers.Serializer):
    """Serializer for create/update field type"""
    field_type_id = serializers.UUIDField(required=False, allow_null=True, help_text="ID for updating existing field type")
    label = serializers.CharField(max_length=50, required=True, help_text="Name/label of the field type")
    type_id = serializers.UUIDField(required=True, help_text="ID of the data type")
    validation_rules = serializers.JSONField(required=False, default=dict, help_text="Validation rules")
    dynamic = serializers.BooleanField(required=False, default=False, help_text="Is dynamic field type")
    end_point = serializers.CharField(max_length=255, required=False, allow_null=True, allow_blank=True, help_text="API endpoint for dynamic data")

    def validate_label(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Field type name is required")
        return value.strip()

    def validate_type_id(self, value):
        if not DataType.objects.filter(id=value).exists():
            raise serializers.ValidationError("Data type does not exist")
        return value

    def validate(self, attrs):
        label = attrs.get('label')
        field_type_id = attrs.get('field_type_id')

        # Check unique name
        qs = FieldType.objects.filter(name=label, is_deleted=False)
        if field_type_id:
            qs = qs.exclude(id=field_type_id)
        if qs.exists():
            raise serializers.ValidationError({"label": "Field type with this name already exists"})

        return attrs

    def create(self, validated_data):
        data_type = DataType.objects.get(id=validated_data['type_id'])
        return FieldType.objects.create(
            name=validated_data['label'],
            data_type=data_type,
            dynamic=validated_data.get('dynamic', False),
            endpoint=validated_data.get('end_point'),
            validation_rules=validated_data.get('validation_rules', {})
        )

    def update(self, instance, validated_data):
        data_type = DataType.objects.get(id=validated_data['type_id'])
        instance.name = validated_data['label']
        instance.data_type = data_type
        instance.dynamic = validated_data.get('dynamic', False)
        instance.endpoint = validated_data.get('end_point')
        instance.validation_rules = validated_data.get('validation_rules', {})
        instance.save(update_fields=['name', 'data_type', 'dynamic', 'endpoint', 'validation_rules', 'updated_on'])
        return instance
