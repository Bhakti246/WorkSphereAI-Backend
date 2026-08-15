from django.contrib import admin
from .models import Employee, Attendance, Leave, Payroll


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "full_name", "email", "department", "is_active")
    search_fields = ("employee_id", "full_name", "email")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "date", "status", "working_hours")
    list_filter = ("status",)


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ("employee", "start_date", "end_date", "status")


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ("employee", "month", "total_salary")
