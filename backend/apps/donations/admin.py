from django.contrib import admin

from .models import Donation


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('donor', 'bloodbank', 'blood_group', 'quantity', 'donation_date', 'status')
    list_filter = ('status', 'blood_group', 'bloodbank')
