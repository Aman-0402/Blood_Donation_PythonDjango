from rest_framework import serializers

from .models import Hospital


class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['id', 'user', 'name', 'address', 'city', 'license_number', 'created_at', 'updated_at']
