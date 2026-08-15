from django.db import models


# Unmanaged mirror models to allow progressive migration.
# These classes point to existing DB tables and are marked managed=False
# so we can refactor code first without forcing migrations changes.


class Employee(models.Model):
    GENDER_CHOICES = (
        ("Male", "Male"),
        ("Female", "Female"),
    )

    employee_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=255)
    photo = models.ImageField(upload_to="employees/", blank=True, null=True)
    face_embedding = models.JSONField(null=True, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    department = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    salary = models.DecimalField(max_digits=12, decimal_places=2)
    joining_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "employees_employee"
        managed = False

    def __str__(self):
        return self.full_name


class Attendance(models.Model):
    STATUS = [
        ("Present", "Present"),
        ("Absent", "Absent"),
        ("Half Day", "Half Day"),
        ("Late", "Late"),
    ]

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="attendance"
    )

    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default="Present")
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "attendance_attendance"
        managed = False
        unique_together = ("employee", "date")

    def __str__(self):
        return f"{self.employee.full_name} - {self.date}"


class Leave(models.Model):
    STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    )

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    reason = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "leaves_leave"
        managed = False

    def __str__(self):
        return self.employee.full_name


class Payroll(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.CharField(max_length=20)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_salary = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payroll_payroll"
        managed = False

    def __str__(self):
        return f"{self.employee.full_name} - {self.month}"
