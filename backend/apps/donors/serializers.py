from rest_framework import serializers

from .models import Donor


class DonorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donor
        fields = [
            'id', 'user', 'blood_group', 'address', 'city', 'date_of_birth',
            'last_donation_date', 'is_available', 'eligibility_notes',
            'created_at', 'updated_at',
        ]
