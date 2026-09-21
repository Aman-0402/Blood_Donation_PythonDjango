from django.contrib import admin

from .models import BloodRequest


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'requester', 'blood_group', 'units_required', 'urgency', 'status', 'created_at')
    list_filter = ('status', 'urgency', 'blood_group')
    search_fields = ('patient_name', 'requester__username', 'location')
