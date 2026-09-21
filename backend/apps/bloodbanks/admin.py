from django.contrib import admin

from .models import BloodBank


@admin.register(BloodBank)
class BloodBankAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'license_number', 'user')
    list_filter = ('city',)
    search_fields = ('name', 'license_number', 'user__username')
