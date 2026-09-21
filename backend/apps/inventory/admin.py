from django.contrib import admin

from .models import BloodInventory, InventoryTransaction


@admin.register(BloodInventory)
class BloodInventoryAdmin(admin.ModelAdmin):
    list_display = ('bloodbank', 'blood_group', 'units', 'collection_date', 'expiry_date', 'status')
    list_filter = ('status', 'blood_group', 'bloodbank')


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'bloodbank', 'blood_group', 'type', 'units', 'request', 'created_by')
    list_filter = ('type', 'blood_group', 'bloodbank')
    readonly_fields = [f.name for f in InventoryTransaction._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
