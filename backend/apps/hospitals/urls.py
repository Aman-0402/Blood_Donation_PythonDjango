from rest_framework.routers import SimpleRouter

from .views import HospitalViewSet

router = SimpleRouter()
router.register('', HospitalViewSet, basename='hospital')
urlpatterns = router.urls
