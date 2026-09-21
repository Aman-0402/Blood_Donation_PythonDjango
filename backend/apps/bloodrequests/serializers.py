from rest_framework import serializers

from apps.accounts.models import Role
from apps.validation import ModelCleanMixin

from .models import BloodRequest, RequestStatusHistory
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
            'units_required', 'urgency', 'location', 'status', 'fulfilled_by_bloodbank',
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

    def validate(self, attrs):
        request = self.context.get('request')
        if self.instance is None and request and request.user.role == Role.HOSPITAL:
            if not hasattr(request.user, 'hospital_profile'):
                raise serializers.ValidationError(
                    'Create your hospital profile before requesting blood.'
                )
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
