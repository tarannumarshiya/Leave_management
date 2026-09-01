from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    RegisterView,
    DashboardRedirectView,
    EmployeeDashboardView,
    ManagerDashboardView,
    AdminDashboardView
)
from .admin_views import (
    DepartmentListView,
    DepartmentCreateView,
    DepartmentUpdateView,
    DepartmentToggleActiveView,
    EmployeeListView,
    EmployeeCreateView,
    EmployeeUpdateView,
    EmployeeToggleActiveView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logged_out.html'), name='logout'),
    
    path('dashboard/', DashboardRedirectView.as_view(), name='dashboard_redirect'),
    path('dashboard/employee/', EmployeeDashboardView.as_view(), name='employee_dashboard'),
    path('dashboard/manager/', ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('dashboard/admin/', AdminDashboardView.as_view(), name='admin_dashboard'),
    
    # Admin Department CRUD
    path('admin-dashboard/departments/', DepartmentListView.as_view(), name='admin_department_list'),
    path('admin-dashboard/departments/create/', DepartmentCreateView.as_view(), name='admin_department_create'),
    path('admin-dashboard/departments/<int:pk>/update/', DepartmentUpdateView.as_view(), name='admin_department_update'),
    path('admin-dashboard/departments/<int:pk>/toggle-active/', DepartmentToggleActiveView.as_view(), name='admin_department_toggle_active'),
    
    # Admin Employee CRUD
    path('admin-dashboard/employees/', EmployeeListView.as_view(), name='admin_employee_list'),
    path('admin-dashboard/employees/create/', EmployeeCreateView.as_view(), name='admin_employee_create'),
    path('admin-dashboard/employees/<int:pk>/update/', EmployeeUpdateView.as_view(), name='admin_employee_update'),
    path('admin-dashboard/employees/<int:pk>/toggle-active/', EmployeeToggleActiveView.as_view(), name='admin_employee_toggle_active'),
]
