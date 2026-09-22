from django.urls import path

from .views import DonationReportView, InventoryReportView, RequestReportView

urlpatterns = [
    path('donations/', DonationReportView.as_view(), name='report-donations'),
    path('requests/', RequestReportView.as_view(), name='report-requests'),
    path('inventory/', InventoryReportView.as_view(), name='report-inventory'),
]
