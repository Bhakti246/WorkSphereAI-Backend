from datetime import date
import numpy as np

from rest_framework.decorators import api_view
from rest_framework.response import Response

from employees.models import Employee
from employees.face_service import get_face_embedding
from attendance.models import Attendance


@api_view(["POST"])
def face_attendance(request):

    if "photo" not in request.FILES:
        return Response({"error": "No image uploaded"}, status=400)

    image = request.FILES["photo"]

    import tempfile

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
        for chunk in image.chunks():
            temp.write(chunk)
        temp_path = temp.name

    embedding = get_face_embedding(temp_path)

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

    if attendance.check_in is None:

        from datetime import datetime

        attendance.check_in = datetime.now().time()

        attendance.status = "Present"

        attendance.save()

    return Response({
        "employee": best_employee.full_name,
        "employee_id": best_employee.employee_id,
        "distance": float(best_distance),
        "status": attendance.status,
        "message": "Attendance Marked Successfully"
    })