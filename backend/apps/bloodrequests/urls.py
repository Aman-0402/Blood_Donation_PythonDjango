from rest_framework.routers import SimpleRouter

from .views import BloodRequestViewSet

router = SimpleRouter()
router.register('', BloodRequestViewSet, basename='bloodrequest')
urlpatterns = router.urls
