from django.contrib import admin

from .models import BloodRequest, RequestStatusHistory


class RequestStatusHistoryInline(admin.TabularInline):
    model = RequestStatusHistory
    extra = 0
    can_delete = False
    readonly_fields = ('from_status', 'to_status', 'changed_by', 'note', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'requester', 'blood_group', 'units_required', 'urgency', 'status', 'created_at')
    list_filter = ('status', 'urgency', 'blood_group')
    search_fields = ('patient_name', 'requester__username', 'location')
    inlines = [RequestStatusHistoryInline]
