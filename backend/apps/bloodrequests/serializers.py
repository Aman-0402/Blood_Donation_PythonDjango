from rest_framework import serializers

from .models import BloodRequest


class BloodRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodRequest
        fields = [
            'id', 'requester', 'hospital', 'patient_name', 'blood_group',
            'units_required', 'urgency', 'location', 'status',
            'fulfilled_by_bloodbank', 'created_at', 'updated_at',
        ]
