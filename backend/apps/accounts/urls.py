from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
    BloodGroupViewSet,
    ChangePasswordView,
    LoginView,
    LogoutView,
    MeView,
    RefreshView,
    RegisterView,
    UserViewSet,
)

user_router = SimpleRouter()
user_router.register('', UserViewSet, basename='user')

blood_group_router = SimpleRouter()
blood_group_router.register('', BloodGroupViewSet, basename='bloodgroup')

user_urlpatterns = user_router.urls
blood_group_urlpatterns = blood_group_router.urls

auth_urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('me/', MeView.as_view(), name='auth-me'),
    path('change-password/', ChangePasswordView.as_view(), name='auth-change-password'),
]
