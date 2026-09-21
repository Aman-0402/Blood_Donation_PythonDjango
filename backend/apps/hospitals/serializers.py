from rest_framework import serializers

from apps.validation import ModelCleanMixin

from .models import Hospital


class HospitalSerializer(ModelCleanMixin, serializers.ModelSerializer):
    is_verified = serializers.BooleanField(source='user.is_verified', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Hospital
        fields = [
            'id', 'user', 'username', 'name', 'address', 'city', 'license_number',
            'is_verified', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_clean_extra(self):
        return {'user': self.context['request'].user}

    def validate_license_number(self, value):
        return value.strip()

    def validate(self, attrs):
        request = self.context.get('request')
        if self.instance is None and request and Hospital.objects.filter(user=request.user).exists():
            raise serializers.ValidationError('A hospital profile already exists for this account.')
        return super().validate(attrs)


class AvailabilityQuerySerializer(serializers.Serializer):
    blood_group = serializers.IntegerField(required=False, min_value=1)
    city = serializers.CharField(required=False, max_length=100)
