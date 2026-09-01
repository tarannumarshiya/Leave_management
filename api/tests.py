from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
import datetime

from users.models import User, Department
from attendance.models import Attendance
from leave.models import LeaveType, LeaveBalance, LeaveRequest

class ApiAuthenticationAndJWTTests(APITestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Engineering", code="ENG")
        self.user = User.objects.create_user(
            username="api_user", password="password123", role="employee", department=self.dept
        )

    def test_jwt_token_obtain_and_use(self):
        # 1. Obtain JWT token
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'api_user',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        access_token = response.data['access']

        # 2. Access protected endpoint using Bearer token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ApiEndpointsPermissionsTests(APITestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Engineering", code="ENG")
        self.employee = User.objects.create_user(
            username="emp_api", password="password", role="employee", department=self.dept
        )
        self.manager = User.objects.create_user(
            username="mgr_api", password="password", role="manager", department=self.dept
        )
        self.employee.manager = self.manager
        self.employee.save()

        self.admin = User.objects.create_user(
            username="adm_api", password="password", role="admin", department=self.dept
        )
        self.leave_type = LeaveType.objects.create(name="Annual Leave", max_days_per_year=15)

    def test_department_create_permission(self):
        # Employee cannot create department
        self.client.force_authenticate(user=self.employee)
        response = self.client.post(reverse('department-list'), {
            'name': 'Finance', 'code': 'FIN'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin can create department
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse('department-list'), {
            'name': 'Finance', 'code': 'FIN'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_leave_request_approval_action(self):
        year = timezone.localdate().year
        LeaveBalance.objects.create(
            employee=self.employee, leave_type=self.leave_type, year=year, total_days=15
        )
        leave_req = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=datetime.date(year, 11, 1),
            end_date=datetime.date(year, 11, 3),
            status='pending',
            reason='Trip'
        )

        # Manager approves via custom action endpoint
        self.client.force_authenticate(user=self.manager)
        approve_url = reverse('leaverequest-approve', kwargs={'pk': leave_req.pk})
        response = self.client.post(approve_url, {'decision_note': 'Approved via API'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        leave_req.refresh_from_db()
        self.assertEqual(leave_req.status, 'approved')
        self.assertEqual(leave_req.approved_by, self.manager)
        self.assertEqual(leave_req.decision_note, 'Approved via API')

    def test_swagger_documentation_endpoint(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get(reverse('swagger-ui'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.get(reverse('schema'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
