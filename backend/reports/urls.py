from django.urls import path
from .views import (
    export_employees,
    export_attendance,
    export_leaves,
    export_payroll,
)

urlpatterns = [
    path("employees/", export_employees),
    path("attendance/", export_attendance),
    path("leaves/", export_leaves),
    path("payroll/", export_payroll),
]