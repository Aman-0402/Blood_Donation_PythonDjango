from rest_framework import serializers

from apps.accounts.models import Role
from apps.validation import ModelCleanMixin

from .models import BloodRequest, DonorResponse, RequestStatusHistory
from .workflow import allowed_next


class BloodRequestSerializer(ModelCleanMixin, serializers.ModelSerializer):
    requester_username = serializers.CharField(source='requester.username', read_only=True)
    hospital_name = serializers.CharField(source='hospital.name', read_only=True, default=None)
    blood_group_name = serializers.CharField(source='blood_group.name', read_only=True)
    fulfilled_by_bloodbank_name = serializers.CharField(
        source='fulfilled_by_bloodbank.name', read_only=True, default=None
    )

    class Meta:
        model = BloodRequest
        fields = [
            'id', 'requester', 'requester_username', 'hospital', 'hospital_name',
            'patient_name', 'contact_phone', 'notes', 'blood_group', 'blood_group_name',
            'units_required', 'urgency', 'city', 'location', 'status', 'fulfilled_by_bloodbank',
            'fulfilled_by_bloodbank_name', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'requester', 'hospital', 'status', 'fulfilled_by_bloodbank',
            'created_at', 'updated_at',
        ]

    def get_clean_extra(self):
        user = self.context['request'].user
        extra = {'requester': user}
        if user.role == Role.HOSPITAL:
            extra['hospital'] = getattr(user, 'hospital_profile', None)
        return extra

    def validate_city(self, value):
        return value.strip()

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.user.role == Role.HOSPITAL:
            profile = getattr(request.user, 'hospital_profile', None)
            if profile is None and self.instance is None:
                raise serializers.ValidationError(
                    'Create your hospital profile before requesting blood.'
                )
            if profile is not None:
                attrs['city'] = profile.city
        return super().validate(attrs)

    PRIVATE_FIELDS = ('requester', 'requester_username', 'patient_name', 'contact_phone', 'notes')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['allowed_next_statuses'] = allowed_next(instance.status)
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is not None and user.role == Role.BLOODBANK:
            bank = getattr(user, 'bloodbank_profile', None)
            if bank is None or instance.fulfilled_by_bloodbank_id != bank.id:
                for field in self.PRIVATE_FIELDS:
                    data.pop(field, None)
        return data


class StatusChangeSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=BloodRequest.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)


class RequestStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True, default=None)

    class Meta:
        model = RequestStatusHistory
        fields = ['id', 'from_status', 'to_status', 'changed_by_username', 'note', 'created_at']


class DonorRequestSerializer(serializers.ModelSerializer):
    """What a donor may see about someone else's request: no patient, requester or contact details."""

    blood_group_name = serializers.CharField(source='blood_group.name', read_only=True)
    hospital_name = serializers.CharField(source='hospital.name', read_only=True, default=None)
    my_response = serializers.SerializerMethodField()

    class Meta:
        model = BloodRequest
        fields = [
            'id', 'blood_group_name', 'units_required', 'urgency', 'city', 'location',
            'hospital_name', 'status', 'created_at', 'my_response',
        ]
        read_only_fields = fields

    def get_my_response(self, instance):
        return self.context.get('responses', {}).get(instance.id)


class DonorResponseListSerializer(serializers.ModelSerializer):
    """Only donors who accepted, and so agreed to share these details with the requester."""

    donor_name = serializers.SerializerMethodField()
    donor_phone = serializers.CharField(source='donor.user.phone', read_only=True)
    blood_group_name = serializers.CharField(source='donor.blood_group.name', read_only=True)
    city = serializers.CharField(source='donor.city', read_only=True)

    class Meta:
        model = DonorResponse
        fields = ['id', 'donor_name', 'donor_phone', 'blood_group_name', 'city', 'updated_at']
        read_only_fields = fields

    def get_donor_name(self, instance):
        user = instance.donor.user
        return user.get_full_name() or user.username


class RespondSerializer(serializers.Serializer):
    answer = serializers.ChoiceField(choices=DonorResponse.Answer.choices)
