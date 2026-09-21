from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import BloodGroup, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_verified', 'is_active')
    list_filter = ('role', 'is_verified', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Blood Donation', {'fields': ('role', 'phone', 'is_verified')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Blood Donation', {'fields': ('email', 'role', 'phone', 'is_verified')}),
    )


@admin.register(BloodGroup)
class BloodGroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
