from django.http import HttpResponse
import csv
from employees.models import Employee
from attendance.models import Attendance
from leaves.models import Leave
from payroll.models import Payroll


def export_employees(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="employees.csv"'

    writer = csv.writer(response)
    writer.writerow(["Employee ID", "Name", "Email", "Department"])

    for employee in Employee.objects.all():
        writer.writerow([
            employee.employee_id,
            employee.full_name,
            employee.email,
            employee.department,
        ])

    return response


def export_attendance(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="attendance.csv"'

    writer = csv.writer(response)
    writer.writerow(["Employee", "Date", "Status"])

    for attendance in Attendance.objects.all():
        writer.writerow([
            attendance.employee.full_name,
            attendance.date,
            attendance.status,
        ])

    return response


def export_leaves(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="leaves.csv"'

    writer = csv.writer(response)
    writer.writerow(["Employee", "Reason", "Status"])

    for leave in Leave.objects.all():
        writer.writerow([
            leave.employee.full_name,
            leave.reason,
            leave.status,
        ])

    return response


def export_payroll(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="payroll.csv"'

    writer = csv.writer(response)
    writer.writerow(["Employee", "Salary", "Bonus", "Total"])

    for payroll in Payroll.objects.all():
        writer.writerow([
            payroll.employee.full_name,
            payroll.salary,
            payroll.bonus,
            payroll.total_salary,
        ])

    return response