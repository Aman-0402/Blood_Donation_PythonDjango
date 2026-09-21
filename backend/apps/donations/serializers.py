from rest_framework import serializers

from apps.accounts.models import Role
from apps.bloodbanks.models import BloodBank

from .models import MAX_DONATION_UNITS, Donation


class DonationSerializer(serializers.ModelSerializer):
    bloodbank_name = serializers.CharField(source='bloodbank.name', read_only=True)
    blood_group_name = serializers.CharField(source='blood_group.name', read_only=True)

    class Meta:
        model = Donation
        fields = [
            'id', 'donor', 'bloodbank', 'bloodbank_name', 'blood_group', 'blood_group_name',
            'quantity', 'donation_date', 'collection_location', 'status', 'rejection_reason',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is not None and user.role in (Role.BLOODBANK, Role.ADMIN):
            donor_user = instance.donor.user
            data['donor_name'] = donor_user.get_full_name() or donor_user.username
            data['donor_phone'] = donor_user.phone
        return data


class ScheduleSerializer(serializers.Serializer):
    bloodbank = serializers.PrimaryKeyRelatedField(queryset=BloodBank.objects.select_related('user'))
    donation_date = serializers.DateField()
    collection_location = serializers.CharField(required=False, allow_blank=True, max_length=255)


class CompleteSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(required=False, default=1, min_value=1, max_value=MAX_DONATION_UNITS)


class RejectSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255)
