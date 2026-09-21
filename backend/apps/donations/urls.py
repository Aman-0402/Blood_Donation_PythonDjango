from rest_framework.routers import SimpleRouter

from .views import DonationViewSet

router = SimpleRouter()
router.register('', DonationViewSet, basename='donation')
urlpatterns = router.urls
