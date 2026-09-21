from rest_framework import serializers

from .models import BloodGroup, User


class BloodGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodGroup
        fields = ['id', 'name']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'role',
            'phone', 'is_verified', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = fields
