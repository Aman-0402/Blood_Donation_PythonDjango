from django.contrib import admin

from .models import Donor


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ('user', 'blood_group', 'city', 'is_available', 'last_donation_date')
    list_filter = ('blood_group', 'is_available', 'city')
    search_fields = ('user__username', 'user__email', 'city')
