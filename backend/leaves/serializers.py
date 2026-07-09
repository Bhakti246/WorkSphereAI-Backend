from rest_framework import serializers
from .models import Leave


class LeaveSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source="employee.full_name",
        read_only=True
    )

    class Meta:
        model = Leave
        fields = [
        "id",
        "employee",
        "employee_name",
        "reason",
        "start_date",
        "end_date",
        "status",
        "created_at",
    ]