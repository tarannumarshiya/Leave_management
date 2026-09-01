from django.test import TestCase
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
import datetime

from users.models import User, Department
from leave.models import LeaveType, LeaveBalance, LeaveRequest
from leave.forms import LeaveRequestForm
from attendance.models import Attendance

class LeaveFormAndValidationTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Engineering", code="ENG")
        self.user = User.objects.create_user(
            username="employee_test", password="password", role="employee", department=self.dept
        )
        self.leave_type = LeaveType.objects.create(name="Annual Leave", max_days_per_year=15)
        
        # Current calendar year
        self.year = timezone.localdate().year
        self.balance = LeaveBalance.objects.create(
            employee=self.user,
            leave_type=self.leave_type,
            year=self.year,
            total_days=15,
            used_days=0
        )

    def test_chronological_dates_validation(self):
        # End date before start date should be invalid
        form_data = {
            'leave_type': self.leave_type.id,
            'start_date': datetime.date(self.year, 9, 10),
            'end_date': datetime.date(self.year, 9, 5),
            'reason': "Vacation"
        }
        form = LeaveRequestForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("End date cannot be before start date.", form.non_field_errors())

    def test_insufficient_balance_validation(self):
        # Attempt to request 16 days (exceeds balance of 15)
        form_data = {
            'leave_type': self.leave_type.id,
            'start_date': datetime.date(self.year, 9, 1),
            'end_date': datetime.date(self.year, 9, 16),
            'reason': "Long vacation"
        }
        form = LeaveRequestForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(any("Insufficient leave balance" in err for err in form.non_field_errors()))

    def test_overlap_validation(self):
        # Create an existing approved leave request from Sep 5 to Sep 8
        LeaveRequest.objects.create(
            employee=self.user,
            leave_type=self.leave_type,
            start_date=datetime.date(self.year, 9, 5),
            end_date=datetime.date(self.year, 9, 8),
            status='approved',
            reason="Existing leave"
        )

        # Attempt to apply for Sep 7 to Sep 10 (overlaps)
        form_data = {
            'leave_type': self.leave_type.id,
            'start_date': datetime.date(self.year, 9, 7),
            'end_date': datetime.date(self.year, 9, 10),
            'reason': "Overlapping trip"
        }
        form = LeaveRequestForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("This request overlaps with an existing pending or approved leave request.", form.non_field_errors())


from django.core import mail

class LeaveSignalAndApprovalTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Engineering", code="ENG")
        self.employee = User.objects.create_user(
            username="employee_test", password="password", role="employee", department=self.dept
        )
        self.manager = User.objects.create_user(
            username="manager_test", password="password", role="manager", department=self.dept
        )
        self.leave_type = LeaveType.objects.create(name="Sick Leave", max_days_per_year=10)
        
        self.year = timezone.localdate().year
        self.balance = LeaveBalance.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            year=self.year,
            total_days=10,
            used_days=0
        )

    def test_leave_approval_triggers_balance_and_attendance(self):
        # 1. Create a pending leave request for 3 days
        request = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=datetime.date(self.year, 10, 1),
            end_date=datetime.date(self.year, 10, 3),
            status='pending',
            reason="Sick"
        )
        
        self.assertEqual(request.duration_days, 3)
        self.assertEqual(self.balance.used_days, 0)
        
        # Verify submission email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("New Leave Request", mail.outbox[0].subject)
        
        # No attendance records yet for these dates
        att_count = Attendance.objects.filter(employee=self.employee, date__range=[request.start_date, request.end_date]).count()
        self.assertEqual(att_count, 0)

        # 2. Approve the leave request
        request.status = 'approved'
        request.approved_by = self.manager
        request.save()  # Fires post_save signal

        # Verify decision email sent
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn("Approved", mail.outbox[1].subject)

        # 3. Verify used days increased
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.used_days, 3)
        self.assertEqual(self.balance.remaining_days, 7)

        # 4. Verify Attendance records generated marked as 'leave'
        attendances = Attendance.objects.filter(employee=self.employee, date__range=[request.start_date, request.end_date])
        self.assertEqual(attendances.count(), 3)
        for att in attendances:
            self.assertEqual(att.status, 'leave')
            self.assertIsNone(att.check_in_time)
            self.assertIsNone(att.check_out_time)
            self.assertEqual(float(att.working_hours), 0.0)


class LeaveAccessControlTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="HR", code="HR")
        self.employee = User.objects.create_user(
            username="emp_user", password="password", role="employee", department=self.dept
        )
        self.manager = User.objects.create_user(
            username="mgr_user", password="password", role="manager", department=self.dept
        )
        self.admin = User.objects.create_user(
            username="adm_user", password="password", role="admin", department=self.dept
        )

    def test_employee_and_manager_access(self):
        # Employee
        self.client.login(username="emp_user", password="password")
        
        # Employee can request leave and list leaves
        response = self.client.get(reverse('leave_apply'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('my_leave_list'))
        self.assertEqual(response.status_code, 200)
        
        # Employee cannot view pending approvals
        response = self.client.get(reverse('pending_approvals_list'))
        self.assertEqual(response.status_code, 403)
        
        # Employee cannot view admin controls
        response = self.client.get(reverse('admin_leave_types'))
        self.assertEqual(response.status_code, 403)

        # Manager
        self.client.login(username="mgr_user", password="password")
        
        # Manager can view pending approvals
        response = self.client.get(reverse('pending_approvals_list'))
        self.assertEqual(response.status_code, 200)
        
        # Manager cannot access admin controls
        response = self.client.get(reverse('admin_leave_types'))
        self.assertEqual(response.status_code, 403)
