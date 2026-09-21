from rest_framework import serializers

from .models import Donation


class DonationSerializer(serializers.ModelSerializer):
    bloodbank_name = serializers.CharField(source='bloodbank.name', read_only=True)
    blood_group_name = serializers.CharField(source='blood_group.name', read_only=True)

    class Meta:
        model = Donation
        fields = [
            'id', 'donor', 'bloodbank', 'bloodbank_name', 'blood_group', 'blood_group_name',
            'quantity', 'donation_date', 'collection_location', 'status',
            'created_at', 'updated_at',
        ]
