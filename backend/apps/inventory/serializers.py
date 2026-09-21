from rest_framework import serializers

from apps.accounts.models import BloodGroup

from .models import MAX_UNITS_PER_OPERATION, BloodInventory, InventoryTransaction


class BloodInventorySerializer(serializers.ModelSerializer):
    blood_group_name = serializers.CharField(source='blood_group.name', read_only=True)
    bloodbank_name = serializers.CharField(source='bloodbank.name', read_only=True)

    class Meta:
        model = BloodInventory
        fields = [
            'id', 'bloodbank', 'bloodbank_name', 'blood_group', 'blood_group_name', 'units',
            'collection_date', 'expiry_date', 'status', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


class CollectionSerializer(serializers.Serializer):
    blood_group = serializers.PrimaryKeyRelatedField(queryset=BloodGroup.objects.all())
    units = serializers.IntegerField(min_value=1, max_value=MAX_UNITS_PER_OPERATION)
    collection_date = serializers.DateField(required=False)
    expiry_date = serializers.DateField(required=False)
    note = serializers.CharField(required=False, allow_blank=True, max_length=255)


class IssueSerializer(serializers.Serializer):
    blood_group = serializers.PrimaryKeyRelatedField(queryset=BloodGroup.objects.all())
    units = serializers.IntegerField(min_value=1, max_value=MAX_UNITS_PER_OPERATION)
    note = serializers.CharField(required=False, allow_blank=True, max_length=255)


class AdjustSerializer(serializers.Serializer):
    delta = serializers.IntegerField()
    reason = serializers.CharField(max_length=255)


class InventoryTransactionSerializer(serializers.ModelSerializer):
    blood_group_name = serializers.CharField(source='blood_group.name', read_only=True)
    bloodbank_name = serializers.CharField(source='bloodbank.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = InventoryTransaction
        fields = [
            'id', 'bloodbank', 'bloodbank_name', 'blood_group', 'blood_group_name', 'batch',
            'type', 'units', 'request', 'note', 'created_by_username', 'created_at',
        ]
        read_only_fields = fields
