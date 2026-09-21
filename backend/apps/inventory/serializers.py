from rest_framework import serializers

from .models import BloodInventory


class BloodInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodInventory
        fields = [
            'id', 'bloodbank', 'blood_group', 'units', 'collection_date',
            'expiry_date', 'status', 'created_at', 'updated_at',
        ]
