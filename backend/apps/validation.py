import copy

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


class ModelCleanMixin:
    """Runs the model's clean() during serializer validation so API writes get the same rules as the admin."""

    def get_clean_extra(self):
        return {}

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance is not None:
            candidate = copy.copy(self.instance)
            data = attrs
        else:
            candidate = self.Meta.model()
            data = {**self.get_clean_extra(), **attrs}
        for key, value in data.items():
            setattr(candidate, key, value)
        try:
            candidate.clean()
        except DjangoValidationError as exc:
            detail = exc.message_dict if hasattr(exc, 'error_dict') else exc.messages
            raise serializers.ValidationError(detail)
        return attrs
