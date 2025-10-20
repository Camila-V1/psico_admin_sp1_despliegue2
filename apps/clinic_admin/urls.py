from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserManagementViewSet

router = DefaultRouter()
router.register(r'users', UserManagementViewSet, basename='clinic-users')

urlpatterns = [
    path('', include(router.urls)),
]
