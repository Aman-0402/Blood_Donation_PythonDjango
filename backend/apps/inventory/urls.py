from rest_framework.routers import SimpleRouter

from .views import BloodInventoryViewSet

router = SimpleRouter()
router.register('', BloodInventoryViewSet, basename='inventory')
urlpatterns = router.urls
