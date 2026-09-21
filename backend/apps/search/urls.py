from django.urls import path

from .views import BloodSearchView, DonorSearchView, HospitalSearchView

urlpatterns = [
    path('blood/', BloodSearchView.as_view(), name='search-blood'),
    path('donors/', DonorSearchView.as_view(), name='search-donors'),
    path('hospitals/', HospitalSearchView.as_view(), name='search-hospitals'),
]
