from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import EmployeeViewSet, dashboard_stats

router = DefaultRouter()
router.register(r'', EmployeeViewSet, basename='employees')

urlpatterns = [
    path('', include(router.urls)),
    path(
        'dashboard-stats/',
        dashboard_stats,
        name='dashboard-stats'
    ),
]