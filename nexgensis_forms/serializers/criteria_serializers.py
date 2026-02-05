from rest_framework import serializers

from ..models import Criteria


class CriteriaSerializer(serializers.ModelSerializer):
    """Serializer for Criteria model - used for read operations"""

    class Meta:
        model = Criteria
        fields = ['id', 'name']
        read_only_fields = ['id']


class CriteriaCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for create/update operations"""
    name = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Name of the criteria"
    )

    class Meta:
        model = Criteria
        fields = ['name']

    def validate_name(self, value):
        """Validate unique name for active records"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")

        value = value.strip()
        instance_id = self.instance.id if self.instance else None

        # Check for unique name among active records only
        qs = Criteria.objects.filter(name__iexact=value, effective_end_date__isnull=True)
        if instance_id:
            qs = qs.exclude(id=instance_id)

        if qs.exists():
            raise serializers.ValidationError("Criteria with this name already exists")
        return value


class CriteriaListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list view"""

    class Meta:
        model = Criteria
        fields = ['id', 'name']
