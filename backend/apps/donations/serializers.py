from rest_framework import serializers

from .models import Donation


class DonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = [
            'id', 'donor', 'bloodbank', 'blood_group', 'quantity', 'donation_date',
            'collection_location', 'status', 'created_at', 'updated_at',
        ]
