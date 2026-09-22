from rest_framework import serializers

from apps.validation import ModelCleanMixin

from .eligibility import compute_eligibility
from .models import Donor


class DonorSerializer(ModelCleanMixin, serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    is_verified = serializers.BooleanField(source='user.is_verified', read_only=True)
    blood_group_name = serializers.CharField(source='blood_group.name', read_only=True)

    class Meta:
        model = Donor
        fields = [
            'id', 'user', 'username', 'is_verified', 'blood_group', 'blood_group_name', 'address',
            'city', 'date_of_birth', 'last_donation_date', 'is_available',
            'eligibility_notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_clean_extra(self):
        return {'user': self.context['request'].user}

    def validate(self, attrs):
        request = self.context.get('request')
        if self.instance is None and request and Donor.objects.filter(user=request.user).exists():
            raise serializers.ValidationError('A donor profile already exists for this account.')
        new_group = attrs.get('blood_group')
        if (
            self.instance is not None
            and new_group is not None
            and new_group != self.instance.blood_group
            and self.instance.donations.exists()
        ):
            raise serializers.ValidationError(
                {'blood_group': 'Blood group cannot be changed once donations are recorded.'}
            )
        return super().validate(attrs)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(compute_eligibility(instance))
        return data
