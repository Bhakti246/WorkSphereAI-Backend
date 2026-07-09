from datetime import date

from django.utils import timezone

from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Attendance
from .serializers import AttendanceSerializer


def calculate_attendance(attendance):

    if (
        attendance.morning_scan and
        attendance.evening_scan
    ):
        return 100

    elif (
        attendance.morning_scan or
        attendance.evening_scan
    ):
        return 50

    return 0


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer


@api_view(["POST"])
def morning_scan(request):

    employee_id = request.data.get("employee_id")

    attendance, created = Attendance.objects.get_or_create(
        employee_id=employee_id,
        date=date.today()
    )

    attendance.morning_scan = timezone.now()

    attendance.attendance_percentage = (
        calculate_attendance(attendance)
    )

    attendance.save()

    return Response({
        "message": "Morning scan successful",
        "attendance_percentage":
        attendance.attendance_percentage
    })


@api_view(["POST"])
def evening_scan(request):

    employee_id = request.data.get("employee_id")

    attendance, created = Attendance.objects.get_or_create(
        employee_id=employee_id,
        date=date.today()
    )

    attendance.evening_scan = timezone.now()

    attendance.attendance_percentage = (
        calculate_attendance(attendance)
    )

    attendance.save()

    return Response({
        "message": "Evening scan successful",
        "attendance_percentage":
        attendance.attendance_percentage
    })


@api_view(["GET"])
def attendance_stats(request):

    total_records = Attendance.objects.count()

    today_present = Attendance.objects.filter(
        date=date.today(),
        attendance_percentage__gt=0
    ).count()

    full_day = Attendance.objects.filter(
        attendance_percentage=100
    ).count()

    half_day = Attendance.objects.filter(
        attendance_percentage=50
    ).count()

    return Response({
        "total_records": total_records,
        "today_present": today_present,
        "full_day": full_day,
        "half_day": half_day,
    })