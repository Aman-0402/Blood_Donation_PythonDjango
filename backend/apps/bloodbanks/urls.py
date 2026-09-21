from rest_framework.routers import SimpleRouter

from .views import BloodBankViewSet

router = SimpleRouter()
router.register('', BloodBankViewSet, basename='bloodbank')
urlpatterns = router.urls
