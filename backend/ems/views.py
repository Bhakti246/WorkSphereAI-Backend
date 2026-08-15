from datetime import date, datetime, time

import numpy as np
import os
from django.utils import timezone
from django.db.models import Count, Q, Sum, Avg

from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.exceptions import PermissionDenied, NotAuthenticated
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from employees.models import Employee
from employees.face_service import get_face_embedding
from employees.serializers import EmployeeSerializer
from attendance.models import Attendance
from attendance.serializers import AttendanceSerializer
from leaves.models import Leave
from leaves.serializers import LeaveSerializer
from payroll.models import Payroll
from payroll.serializers import PayrollSerializer
from .permissions import RolePermission, user_roles
from django.http import HttpResponse
import csv
import tempfile


WORK_START = time(9, 0)
LATE_AFTER = time(9, 30)
WORK_END = time(17, 30)
MIN_HALF_DAY_HOURS = 4.0
FULL_DAY_HOURS = 8.0


def calculate_attendance(attendance):
    if attendance.check_in and attendance.check_out:
        return 100
    if attendance.check_in or attendance.check_out:
        return 50
    return 0


def evaluate_attendance(attendance):
    if not attendance.check_in and not attendance.check_out:
        return "Absent"

    if not attendance.check_in or not attendance.check_out:
        return "Half Day"

    if attendance.working_hours < MIN_HALF_DAY_HOURS:
        return "Half Day"

    if attendance.check_in > LATE_AFTER:
        return "Late"

    return "Present"


def calculate_overtime(attendance):
    working_hours = float(attendance.working_hours or 0)
    return round(max(working_hours - FULL_DAY_HOURS, 0), 2)


def normalize_time(value):
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%H:%M:%S").time()
        except ValueError:
            return None
    return value


def user_has_roles(user, allowed_roles):
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True
    return bool(user_roles(user).intersection(set(allowed_roles)))


def validate_staff_access(request, allowed_roles):
    if not request.user or not request.user.is_authenticated:
        raise NotAuthenticated(detail="Authentication credentials were not provided.")
    if not user_has_roles(request.user, allowed_roles):
        raise PermissionDenied(detail="You do not have permission to perform this action.")


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, RolePermission]
    allowed_roles = ["Admin", "HR", "Manager", "Employee"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if not user or not user.is_authenticated:
            return queryset.none()

        if user_has_roles(user, {"Admin", "HR", "Manager"}):
            queryset = queryset
        else:
            queryset = queryset.filter(email__iexact=user.email)

        query = self.request.query_params.get("q")
        department = self.request.query_params.get("department")

        if query:
            queryset = queryset.filter(
                Q(full_name__icontains=query)
                | Q(employee_id__icontains=query)
                | Q(email__icontains=query)
            )

        if department:
            queryset = queryset.filter(department__iexact=department)

        return queryset

    def create(self, request, *args, **kwargs):
        if not user_has_roles(request.user, {"Admin", "HR", "Manager"}):
            raise PermissionDenied("Only Admin, HR, or Manager can create employees.")
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not user_has_roles(request.user, {"Admin", "HR", "Manager"}):
            raise PermissionDenied("Only Admin, HR, or Manager can delete employees.")
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        employee = serializer.save()

        if getattr(employee, 'photo', None):
            embedding = get_face_embedding(employee.photo.path)
            if embedding:
                employee.face_embedding = embedding
                employee.save()

    def perform_update(self, serializer):
        employee = serializer.save()
        if getattr(employee, 'photo', None):
            embedding = get_face_embedding(employee.photo.path)
            if embedding:
                employee.face_embedding = embedding
                employee.save()

    @action(detail=True, methods=["post"], url_path="register-face")
    def register_face(self, request, pk=None):
        if "photo" not in request.FILES:
            return Response({"error": "No photo uploaded"}, status=400)

        employee = self.get_object()
        image = request.FILES["photo"]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
            for chunk in image.chunks():
                temp.write(chunk)
            temp_path = temp.name

        try:
            embedding = get_face_embedding(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        if embedding is None:
            return Response({"error": "Face not detected"}, status=400)

        employee.face_embedding = embedding
        employee.save()

        return Response({"message": "Face Registered Successfully"})

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        queryset = self.get_queryset()
        departments = (
            queryset.values("department")
            .annotate(count=Count("id"))
            .order_by("department")
        )
        total = queryset.count()
        return Response({
            "total_employees": total,
            "departments": list(departments),
        })


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, RolePermission]
    allowed_roles = ["Admin", "HR", "Manager", "Employee"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if not user or not user.is_authenticated:
            return queryset.none()

        if user_has_roles(user, {"Admin", "HR", "Manager"}):
            queryset = queryset
        else:
            queryset = queryset.filter(employee__email=user.email)

        employee_id = self.request.query_params.get("employee_id")
        date_param = self.request.query_params.get("date")
        status = self.request.query_params.get("status")

        if employee_id:
            queryset = queryset.filter(employee__employee_id__iexact=employee_id)

        if date_param:
            try:
                filter_date = datetime.strptime(date_param, "%Y-%m-%d").date()
                queryset = queryset.filter(date=filter_date)
            except ValueError:
                pass

        if status:
            queryset = queryset.filter(status__iexact=status)

        return queryset

    def perform_create(self, serializer):
        attendance = serializer.save()
        update_attendance_record(attendance)
        attendance.save()

    def perform_update(self, serializer):
        attendance = serializer.save()
        update_attendance_record(attendance)
        attendance.save()

    @action(detail=False, methods=["post"], url_path="face")
    def face_attendance(self, request):
        if "photo" not in request.FILES:
            return Response({"error": "No image uploaded"}, status=400)

        image = request.FILES["photo"]

        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
            for chunk in image.chunks():
                temp.write(chunk)
            temp_path = temp.name

        try:
            embedding = get_face_embedding(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        if embedding is None:
            return Response({"error": "Face not detected"}, status=400)

        embedding = np.array(embedding)
        best_employee = None
        best_distance = 999

        employees = Employee.objects.exclude(face_embedding=None)

        for emp in employees:
            db_embedding = np.array(emp.face_embedding)
            distance = np.linalg.norm(db_embedding - embedding)
            if distance < best_distance:
                best_distance = distance
                best_employee = emp

        if best_employee is None:
            return Response({"error": "Unknown Person"}, status=404)

        attendance, created = Attendance.objects.get_or_create(
            employee=best_employee,
            date=date.today()
        )

        now_time = timezone.now().time()
        event = "none"

        if attendance.check_in is None:
            attendance.check_in = now_time
            event = "check_in"
        elif attendance.check_out is None:
            attendance.check_out = now_time
            event = "check_out"
        else:
            update_attendance_record(attendance)
            attendance.save()
            return Response({
                "employee": best_employee.full_name,
                "employee_id": best_employee.employee_id,
                "status": attendance.status,
                "working_hours": float(attendance.working_hours or 0),
                "overtime_hours": float(attendance.overtime_hours or 0),
                "message": "Attendance already complete for today",
            })

        update_attendance_record(attendance)
        attendance.save()

        return Response({
            "employee": best_employee.full_name,
            "employee_id": best_employee.employee_id,
            "distance": float(best_distance),
            "event": event,
            "status": attendance.status,
            "working_hours": float(attendance.working_hours or 0),
            "overtime_hours": float(attendance.overtime_hours or 0),
            "message": "Attendance marked successfully",
        })

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        totals = self.get_queryset().values("status").annotate(count=Count("id"))
        present_today = self.get_queryset().filter(
            date=date.today(),
        ).filter(Q(check_in__isnull=False) | Q(check_out__isnull=False)).count()
        return Response({
            "total_records": self.get_queryset().count(),
            "present_today": present_today,
            "status_summary": list(totals),
        })


def update_attendance_record(attendance):
    if attendance.check_in and attendance.check_out:
        dt_in = datetime.combine(attendance.date, attendance.check_in)
        dt_out = datetime.combine(attendance.date, attendance.check_out)
        delta = dt_out - dt_in
        attendance.working_hours = round(max(delta.total_seconds(), 0) / 3600, 2)
        attendance.overtime_hours = calculate_overtime(attendance)
        attendance.status = evaluate_attendance(attendance)
    else:
        attendance.working_hours = 0
        attendance.overtime_hours = 0
        attendance.status = evaluate_attendance(attendance)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def morning_scan(request):
    employee_identifier = request.data.get("employee_id")

    if not employee_identifier:
        return Response({"error": "employee_id is required"}, status=400)

    try:
        employee = Employee.objects.get(employee_id=employee_identifier)
    except Employee.DoesNotExist:
        return Response({"error": "Employee not found"}, status=404)

    attendance, created = Attendance.objects.get_or_create(
        employee=employee,
        date=date.today(),
    )

    attendance.check_in = timezone.now().time()
    update_attendance_record(attendance)
    attendance.save()

    return Response({
        "message": "Morning scan successful",
        "attendance_percentage": calculate_attendance(attendance),
        "status": attendance.status,
        "working_hours": float(attendance.working_hours or 0),
        "overtime_hours": float(attendance.overtime_hours or 0),
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def evening_scan(request):
    employee_identifier = request.data.get("employee_id")

    if not employee_identifier:
        return Response({"error": "employee_id is required"}, status=400)

    try:
        employee = Employee.objects.get(employee_id=employee_identifier)
    except Employee.DoesNotExist:
        return Response({"error": "Employee not found"}, status=404)

    attendance, created = Attendance.objects.get_or_create(
        employee=employee,
        date=date.today(),
    )

    attendance.check_out = timezone.now().time()
    update_attendance_record(attendance)
    attendance.save()

    return Response({
        "message": "Evening scan successful",
        "attendance_percentage": calculate_attendance(attendance),
        "status": attendance.status,
        "working_hours": float(attendance.working_hours or 0),
        "overtime_hours": float(attendance.overtime_hours or 0),
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def attendance_stats(request):
    from django.db.models import Q

    user = request.user
    queryset = Attendance.objects.all()
    if not user_has_roles(user, {"Admin", "HR", "Manager"}):
        queryset = queryset.filter(employee__email=user.email)

    total_records = queryset.count()

    today_present = queryset.filter(
        date=date.today(),
    ).filter(Q(check_in__isnull=False) | Q(check_out__isnull=False)).count()

    full_day = queryset.filter(
        check_in__isnull=False, check_out__isnull=False
    ).count()

    half_day = queryset.filter(
        (Q(check_in__isnull=False) & Q(check_out__isnull=True))
        | (Q(check_in__isnull=True) & Q(check_out__isnull=False))
    ).count()

    return Response(
        {
            "total_records": total_records,
            "today_present": today_present,
            "full_day": full_day,
            "half_day": half_day,
        }
    )


class LeaveViewSet(viewsets.ModelViewSet):
    queryset = Leave.objects.all()
    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated, RolePermission]
    allowed_roles = ["Admin", "HR", "Manager", "Employee"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if not user or not user.is_authenticated:
            return queryset.none()

        if user_has_roles(user, {"Admin", "HR", "Manager"}):
            return queryset

        return queryset.filter(employee__email=user.email)

    def perform_create(self, serializer):
        serializer.save(status="Pending")

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        if not user_has_roles(request.user, {"Admin", "HR", "Manager"}):
            raise PermissionDenied("Only Admin, HR, or Manager can approve leaves.")

        leave = self.get_object()
        leave.status = "Approved"
        leave.save()

        return Response({"message": "Leave approved"})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        if not user_has_roles(request.user, {"Admin", "HR", "Manager"}):
            raise PermissionDenied("Only Admin, HR, or Manager can reject leaves.")

        leave = self.get_object()
        leave.status = "Rejected"
        leave.save()

        return Response({"message": "Leave rejected"})

    @action(detail=False, methods=["get"], url_path="pending")
    def pending(self, request):
        pending_leaves = self.get_queryset().filter(status="Pending")
        serializer = self.get_serializer(pending_leaves, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        totals = self.get_queryset().values("status").annotate(count=Count("id"))
        upcoming = self.get_queryset().filter(start_date__gte=date.today()).count()
        return Response({
            "summary": list(totals),
            "upcoming_leaves": upcoming,
        })


class PayrollViewSet(viewsets.ModelViewSet):
    queryset = Payroll.objects.all()
    serializer_class = PayrollSerializer
    permission_classes = [IsAuthenticated, RolePermission]
    allowed_roles = ["Admin", "HR"]

    def perform_create(self, serializer):
        salary = serializer.validated_data.get("salary") or 0
        bonus = serializer.validated_data.get("bonus") or 0
        deductions = serializer.validated_data.get("deductions") or 0
        total_salary = serializer.validated_data.get("total_salary")
        if total_salary is None:
            total_salary = salary + bonus - deductions
        serializer.save(total_salary=total_salary)

    def perform_update(self, serializer):
        salary = serializer.validated_data.get("salary") or serializer.instance.salary
        bonus = serializer.validated_data.get("bonus") or serializer.instance.bonus
        deductions = serializer.validated_data.get("deductions") or serializer.instance.deductions
        total_salary = serializer.validated_data.get("total_salary")
        if total_salary is None:
            total_salary = salary + bonus - deductions
        serializer.save(total_salary=total_salary)

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        totals = self.get_queryset().aggregate(
            total_payroll=Sum("total_salary"),
            average_salary=Avg("total_salary"),
            total_bonus=Sum("bonus"),
            total_deductions=Sum("deductions"),
        )
        return Response({
            "total_payroll": float(totals["total_payroll"] or 0),
            "average_salary": float(totals["average_salary"] or 0),
            "total_bonus": float(totals["total_bonus"] or 0),
            "total_deductions": float(totals["total_deductions"] or 0),
        })

    @action(detail=False, methods=["get"], url_path="monthly-summary")
    def monthly_summary(self, request):
        monthly = self.get_queryset().values("month").annotate(
            total_payroll=Sum("total_salary"),
            total_bonus=Sum("bonus"),
            total_deductions=Sum("deductions"),
            count=Count("id"),
        ).order_by("month")
        return Response({"monthly_summary": list(monthly)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    is_staff_role = user_has_roles(request.user, {"Admin", "HR", "Manager"})
    employee_queryset = Employee.objects.all()
    attendance_queryset = Attendance.objects.all()
    leave_queryset = Leave.objects.all()

    if not is_staff_role:
        employee_queryset = employee_queryset.filter(email__iexact=request.user.email)
        attendance_queryset = attendance_queryset.filter(employee__email__iexact=request.user.email)
        leave_queryset = leave_queryset.filter(employee__email__iexact=request.user.email)

    total_employees = employee_queryset.count()

    present_today = attendance_queryset.filter(
        date=date.today(),
        check_in__isnull=False
    ).count()

    on_leave = leave_queryset.filter(
        status="Approved",
        start_date__lte=date.today(),
        end_date__gte=date.today(),
    ).count()

    payroll_counts = Payroll.objects.count() if is_staff_role else Payroll.objects.filter(employee__email__iexact=request.user.email).count()

    total_salary_agg = employee_queryset.aggregate(total=Sum('salary'))
    total_salary = float(total_salary_agg.get('total') or 0)
    return Response({
        "total_employees": total_employees,
        "present_today": present_today,
        "on_leave": on_leave,
        "payroll": payroll_counts,
        "total_salary": total_salary,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_employees(request):
    validate_staff_access(request, {"Admin", "HR", "Manager"})

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="employees.csv"'

    writer = csv.writer(response)
    writer.writerow(["Employee ID", "Name", "Email", "Department"])

    for employee in Employee.objects.all():
        writer.writerow([
            employee.employee_id,
            getattr(employee, 'full_name', ''),
            getattr(employee, 'email', ''),
            getattr(employee, 'department', ''),
        ])

    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_attendance(request):
    validate_staff_access(request, {"Admin", "HR", "Manager"})

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="attendance.csv"'

    writer = csv.writer(response)
    writer.writerow(["Employee", "Date", "Status"])

    for attendance in Attendance.objects.all():
        writer.writerow([
            getattr(attendance.employee, 'full_name', ''),
            attendance.date,
            getattr(attendance, 'status', ''),
        ])

    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_leaves(request):
    validate_staff_access(request, {"Admin", "HR", "Manager"})

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="leaves.csv"'

    writer = csv.writer(response)
    writer.writerow(["Employee", "Reason", "Status"])

    for leave in Leave.objects.all():
        writer.writerow([
            getattr(leave.employee, 'full_name', ''),
            getattr(leave, 'reason', ''),
            getattr(leave, 'status', ''),
        ])

    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_payroll(request):
    validate_staff_access(request, {"Admin", "HR"})

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="payroll.csv"'

    writer = csv.writer(response)
    writer.writerow(["Employee", "Salary", "Bonus", "Total"])

    for payroll in Payroll.objects.all():
        writer.writerow([
            getattr(payroll.employee, 'full_name', ''),
            getattr(payroll, 'salary', ''),
            getattr(payroll, 'bonus', ''),
            getattr(payroll, 'total_salary', ''),
        ])

    return response
