from rest_framework.routers import SimpleRouter

from .views import DonorViewSet

router = SimpleRouter()
router.register('', DonorViewSet, basename='donor')
urlpatterns = router.urls
