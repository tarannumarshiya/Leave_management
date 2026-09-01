from django.test import TestCase
from django.urls import reverse
from users.models import User, Department

class AdminAccessControlTests(TestCase):
    def setUp(self):
        # Create department
        self.dept = Department.objects.create(name="Engineering", code="ENG")
        
        # Create Employee user
        self.employee = User.objects.create_user(
            username="employee_test",
            password="password",
            role="employee",
            department=self.dept
        )
        
        # Create Manager user
        self.manager = User.objects.create_user(
            username="manager_test",
            password="password",
            role="manager",
            department=self.dept
        )
        
        # Create Admin user
        self.admin = User.objects.create_user(
            username="admin_test",
            password="password",
            role="admin",
            department=self.dept
        )

    def test_unauthenticated_redirect(self):
        # Test department list redirects to login
        response = self.client.get(reverse('admin_department_list'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('admin_department_list')}")
        
        # Test employee list redirects to login
        response = self.client.get(reverse('admin_employee_list'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('admin_employee_list')}")

    def test_employee_forbidden(self):
        # Log in as employee
        self.client.login(username="employee_test", password="password")
        
        # Access department list - should raise 403
        response = self.client.get(reverse('admin_department_list'))
        self.assertEqual(response.status_code, 403)
        
        # Access employee list - should raise 403
        response = self.client.get(reverse('admin_employee_list'))
        self.assertEqual(response.status_code, 403)

    def test_manager_forbidden(self):
        # Log in as manager
        self.client.login(username="manager_test", password="password")
        
        # Access department list - should raise 403
        response = self.client.get(reverse('admin_department_list'))
        self.assertEqual(response.status_code, 403)
        
        # Access employee list - should raise 403
        response = self.client.get(reverse('admin_employee_list'))
        self.assertEqual(response.status_code, 403)

    def test_admin_allowed(self):
        # Log in as admin
        self.client.login(username="admin_test", password="password")
        
        # Access department list - should return 200 OK
        response = self.client.get(reverse('admin_department_list'))
        self.assertEqual(response.status_code, 200)
        
        # Access employee list - should return 200 OK
        response = self.client.get(reverse('admin_employee_list'))
        self.assertEqual(response.status_code, 200)
