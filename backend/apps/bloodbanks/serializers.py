from rest_framework import serializers

from .models import BloodBank


class BloodBankSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodBank
        fields = ['id', 'user', 'name', 'address', 'city', 'license_number', 'created_at', 'updated_at']
