from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.urls import path
from .face_views import face_attendance

from .views import (
    AttendanceViewSet,
    morning_scan,
    evening_scan,
    attendance_stats
)

router = DefaultRouter()

router.register(
    'attendance',
    AttendanceViewSet
)

urlpatterns = [

    path(
        "",
        include(router.urls)
    ),

    path(
        "morning-scan/",
        morning_scan
    ),

    path(
        "evening-scan/",
        evening_scan
    ),

    path(
        "attendance-stats/",
        attendance_stats
    ),
    path("face/", face_attendance),
]