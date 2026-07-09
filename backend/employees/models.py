from django.db import models

class Employee(models.Model):
    GENDER_CHOICES = (
        ("Male", "Male"),
        ("Female", "Female"),
    )

    employee_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=255)
    photo = models.ImageField(
    upload_to="employees/",
    blank=True,
    null=True
)

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    department = models.CharField(max_length=100)
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES
    )

    salary = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    joining_date = models.DateField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name