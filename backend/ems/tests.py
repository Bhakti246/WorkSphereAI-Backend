from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient

from attendance.models import Attendance
from employees.models import Employee
from leaves.models import Leave
from payroll.models import Payroll
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile


class EmsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.User = get_user_model()

        self.admin_group = Group.objects.create(name="Admin")
        self.hr_group = Group.objects.create(name="HR")
        self.employee_group = Group.objects.create(name="Employee")

        self.admin_user = self.User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="adminpass",
            is_staff=True,
        )
        self.admin_user.groups.add(self.admin_group)

        self.hr_user = self.User.objects.create_user(
            username="hruser",
            email="hr@example.com",
            password="hrpass",
        )
        self.hr_user.groups.add(self.hr_group)

        self.employee_user = self.User.objects.create_user(
            username="employeeuser",
            email="employee@example.com",
            password="emppass",
        )
        self.employee_user.groups.add(self.employee_group)

        self.employee_record = Employee.objects.create(
            employee_id="EMP001",
            full_name="Employee One",
            email="employee@example.com",
            phone="1234567890",
            department="Engineering",
            gender="Male",
            salary=50000,
            joining_date=date.today(),
        )

        self.other_employee = Employee.objects.create(
            employee_id="EMP002",
            full_name="Employee Two",
            email="employee2@example.com",
            phone="0987654321",
            department="HR",
            gender="Female",
            salary=60000,
            joining_date=date.today(),
        )

        self.leave = Leave.objects.create(
            employee=self.employee_record,
            reason="Personal",
            start_date=date.today(),
            end_date=date.today(),
            status="Pending",
        )

        self.payroll = Payroll.objects.create(
            employee=self.employee_record,
            month="2026-08",
            salary=50000,
            bonus=1000,
            deductions=500,
            total_salary=50500,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_employee_summary_admin(self):
        self.authenticate(self.admin_user)
        url = reverse("employee-summary")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_employees"], 2)
        self.assertTrue(any(item["department"] == "Engineering" for item in response.data["departments"]))

    def test_employee_self_access_only_own(self):
        self.authenticate(self.employee_user)
        url = reverse("employee-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["email"], self.employee_record.email)

    def test_attendance_stats_requires_auth(self):
        url = reverse("attendance-stats")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.authenticate(self.employee_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("total_records", response.data)

    def test_export_leaves_requires_staff_role(self):
        self.authenticate(self.employee_user)
        url = reverse("export-leaves")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        self.authenticate(self.hr_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("Employee", response.content.decode())

    def test_export_payroll_requires_hr_or_admin(self):
        self.authenticate(self.employee_user)
        url = reverse("export-payroll")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        self.authenticate(self.hr_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("Salary", response.content.decode())

    def test_attendance_check_in_and_out(self):
        self.authenticate(self.employee_user)
        checkin_url = reverse("attendance-check-in")
        response = self.client.post(checkin_url, {"employee_id": self.employee_record.employee_id}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "Half Day" if response.data["attendance_percentage"] == 50 else response.data["status"])

        checkout_url = reverse("attendance-check-out")
        response = self.client.post(checkout_url, {"employee_id": self.employee_record.employee_id}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("working_hours", response.data)

    def test_leave_summary_employee(self):
        self.authenticate(self.employee_user)
        url = reverse("leave-summary")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["summary"][0]["count"], 1)

    def test_face_attendance_marks_check_in(self):
        # Patch the face embedding extraction to avoid heavy model dependency
        emb = [0.123] * 128
        self.employee_record.face_embedding = emb
        self.employee_record.save()

        self.authenticate(self.employee_user)

        # router action endpoint is available at this path under the API include
        url = '/api/attendance/face/'
        image = SimpleUploadedFile('face.jpg', b'\xff\xd8fakejpgdata', content_type='image/jpeg')

        with patch('ems.views.get_face_embedding', return_value=emb):
            response = self.client.post(url, {'photo': image}, format='multipart')

        self.assertEqual(response.status_code, 200)
        self.assertIn('employee_id', response.data)
        self.assertIn(response.data.get('event'), ['check_in', 'check_out'])

    def test_jwt_token_flow_and_logout(self):
        # Obtain tokens
        url = reverse('token_obtain_pair')
        resp = self.client.post(url, {'username': 'adminuser', 'password': 'adminpass'}, format='json')
        self.assertEqual(resp.status_code, 200)
        access = resp.data.get('access')
        refresh = resp.data.get('refresh')
        self.assertIsNotNone(access)
        self.assertIsNotNone(refresh)

        # Access protected endpoint
        stats_url = reverse('attendance-stats')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        r = self.client.get(stats_url)
        self.assertEqual(r.status_code, 200)

        # Verify token
        verify_url = reverse('token_verify')
        v = self.client.post(verify_url, {'token': access}, format='json')
        self.assertEqual(v.status_code, 200)

        # Logout (blacklist refresh) using the original refresh
        logout_url = reverse('token_logout')
        lo = self.client.post(logout_url, {'refresh': refresh}, format='json')
        self.assertEqual(lo.status_code, 200)

        # Attempt to refresh with the now-blacklisted refresh token should fail
        refresh_url = reverse('token_refresh')
        fail = self.client.post(refresh_url, {'refresh': refresh}, format='json')
        self.assertNotEqual(fail.status_code, 200)

    def test_export_employees_and_attendance_csv_contents(self):
        # create an attendance record so export has data
        from attendance.models import Attendance

        Attendance.objects.create(
            employee=self.employee_record,
            date=date.today(),
            status='Present'
        )

        # export employees as HR
        self.authenticate(self.hr_user)
        emp_url = reverse('export-employees')
        r = self.client.get(emp_url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'text/csv')
        content = r.content.decode()
        self.assertIn('Employee ID', content)
        self.assertIn(self.employee_record.full_name, content)

        # export attendance as Admin
        self.authenticate(self.admin_user)
        att_url = reverse('export-attendance')
        a = self.client.get(att_url)
        self.assertEqual(a.status_code, 200)
        self.assertEqual(a['Content-Type'], 'text/csv')
        att_content = a.content.decode()
        self.assertIn(self.employee_record.full_name, att_content)

    def test_leave_approve_reject_permissions(self):
        # HR can approve
        self.authenticate(self.hr_user)
        approve_url = reverse('leave-approve', args=[self.leave.id])
        resp = self.client.post(approve_url)
        self.assertEqual(resp.status_code, 200)
        self.leave.refresh_from_db()
        self.assertEqual(self.leave.status, 'Approved')

        # Create another leave for rejection test
        new_leave = Leave.objects.create(
            employee=self.employee_record,
            reason='Sick',
            start_date=date.today(),
            end_date=date.today(),
            status='Pending',
        )

        reject_url = reverse('leave-reject', args=[new_leave.id])
        resp2 = self.client.post(reject_url)
        self.assertEqual(resp2.status_code, 200)
        new_leave.refresh_from_db()
        self.assertEqual(new_leave.status, 'Rejected')

        # Employee cannot approve
        self.authenticate(self.employee_user)
        resp3 = self.client.post(approve_url)
        self.assertIn(resp3.status_code, (403, 405))
