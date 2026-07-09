from datetime import date

from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Employee
from .serializers import EmployeeSerializer

from attendance.models import Attendance
from payroll.models import Payroll


# Employee CRUD API
class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer


# Dashboard API
@api_view(["GET"])
@permission_classes([AllowAny])
def dashboard_stats(request):

    total_employees = Employee.objects.count()

    present_today = Attendance.objects.filter(
        date=date.today(),
        check_in__isnull=False
    ).count()

    on_leave = Attendance.objects.filter(
        date=date.today(),
        status="Leave"
    ).count()

    payroll_counts = Payroll.objects.count()

    total_salary = sum(
        float(emp.salary or 0)
        for emp in Employee.objects.all()
    )

    return Response({
        "total_employees": total_employees,
        "present_today": present_today,
        "on_leave": on_leave,
        "payroll": payroll_counts,
        "total_salary": total_salary,
    })