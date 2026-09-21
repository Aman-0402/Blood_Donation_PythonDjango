from django.contrib import admin
from django.urls import include, path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts import urls as accounts_urls


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({'status': 'ok'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),
    path('api/auth/', include(accounts_urls.auth_urlpatterns)),
    path('api/users/', include(accounts_urls.user_urlpatterns)),
    path('api/blood-groups/', include(accounts_urls.blood_group_urlpatterns)),
    path('api/donors/', include('apps.donors.urls')),
    path('api/hospitals/', include('apps.hospitals.urls')),
    path('api/bloodbanks/', include('apps.bloodbanks.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
    path('api/donations/', include('apps.donations.urls')),
    path('api/requests/', include('apps.bloodrequests.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
]
