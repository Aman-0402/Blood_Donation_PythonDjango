from rest_framework.routers import SimpleRouter

from .views import BloodGroupViewSet, UserViewSet

user_router = SimpleRouter()
user_router.register('', UserViewSet, basename='user')

blood_group_router = SimpleRouter()
blood_group_router.register('', BloodGroupViewSet, basename='bloodgroup')

user_urlpatterns = user_router.urls
blood_group_urlpatterns = blood_group_router.urls
