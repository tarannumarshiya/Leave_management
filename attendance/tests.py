from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone
import datetime

from users.models import User, Department
from attendance.models import Attendance

class AttendanceModelTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Engineering", code="ENG")
        self.user = User.objects.create_user(
            username="employee_test",
            password="password",
            role="employee",
            department=self.dept
        )

    def test_working_hours_calculation(self):
        # 9:00 AM to 5:00 PM is exactly 8 hours
        record = Attendance.objects.create(
            employee=self.user,
            date=timezone.localdate(),
            check_in_time=datetime.time(9, 0),
            check_out_time=datetime.time(17, 0)
        )
        self.assertEqual(float(record.working_hours), 8.0)

    def test_invalid_times_validation(self):
        # Check-out time before check-in time should raise validation error
        record = Attendance(
            employee=self.user,
            date=timezone.localdate(),
            check_in_time=datetime.time(17, 0),
            check_out_time=datetime.time(9, 0)
        )
        with self.assertRaises(ValidationError):
            record.full_clean()

    def test_duplicate_attendance_constraint(self):
        today = timezone.localdate()
        Attendance.objects.create(
            employee=self.user,
            date=today,
            check_in_time=datetime.time(9, 0)
        )
        
        # Creating second record for the same employee and date should raise IntegrityError
        with self.assertRaises(IntegrityError):
            Attendance.objects.create(
                employee=self.user,
                date=today,
                check_in_time=datetime.time(13, 0)
            )


class AttendanceViewAccessTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Engineering", code="ENG")
        
        # Employee
        self.employee = User.objects.create_user(
            username="emp_test", password="password", role="employee", department=self.dept
        )
        # Manager
        self.manager = User.objects.create_user(
            username="mgr_test", password="password", role="manager", department=self.dept
        )
        # Admin
        self.admin = User.objects.create_user(
            username="adm_test", password="password", role="admin", department=self.dept
        )

    def test_employee_access_restrictions(self):
        self.client.login(username="emp_test", password="password")
        
        # Can access self history
        response = self.client.get(reverse('my_attendance_list'))
        self.assertEqual(response.status_code, 200)
        
        # Cannot access team attendance
        response = self.client.get(reverse('team_attendance_list'))
        self.assertEqual(response.status_code, 403)
        
        # Cannot access org attendance
        response = self.client.get(reverse('org_attendance_list'))
        self.assertEqual(response.status_code, 403)

    def test_manager_access(self):
        self.client.login(username="mgr_test", password="password")
        
        # Can access team attendance
        response = self.client.get(reverse('team_attendance_list'))
        self.assertEqual(response.status_code, 200)
        
        # Cannot access org attendance
        response = self.client.get(reverse('org_attendance_list'))
        self.assertEqual(response.status_code, 403)

    def test_admin_access(self):
        self.client.login(username="adm_test", password="password")
        
        # Can access org attendance
        response = self.client.get(reverse('org_attendance_list'))
        self.assertEqual(response.status_code, 200)
        
        # Can export org attendance
        response = self.client.get(reverse('export_attendance_csv'))
        self.assertEqual(response.status_code, 200)
