from django.contrib import admin

from .models import BloodInventory


@admin.register(BloodInventory)
class BloodInventoryAdmin(admin.ModelAdmin):
    list_display = ('bloodbank', 'blood_group', 'units', 'collection_date', 'expiry_date', 'status')
    list_filter = ('status', 'blood_group', 'bloodbank')
