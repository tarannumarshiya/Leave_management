from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.core.exceptions import PermissionDenied

from .models import User, Department
from .forms import DepartmentForm, EmployeeAdminForm

class AdminRequiredMixin(UserPassesTestMixin):
    """
    Restricts access to only admin users or superusers.
    """
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.role == 'admin' or self.request.user.is_superuser
        )

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You do not have permission to access that administrative page.")
        return super().handle_no_permission()


# Department CRUD Views

class DepartmentListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Department
    template_name = 'admin_dashboard/department_list.html'
    context_object_name = 'departments'
    paginate_by = 10

    def get_queryset(self):
        queryset = Department.objects.all().order_by('name')
        q = self.request.GET.get('q', '')
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(code__icontains=q)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['title'] = 'Manage Departments'
        return context


class DepartmentCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'admin_dashboard/department_form.html'
    success_url = reverse_lazy('admin_department_list')

    def form_valid(self, form):
        messages.success(self.request, f"Department '{form.cleaned_data['name']}' created successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Department'
        return context


class DepartmentUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'admin_dashboard/department_form.html'
    success_url = reverse_lazy('admin_department_list')

    def form_valid(self, form):
        messages.success(self.request, f"Department '{form.cleaned_data['name']}' updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Edit Department: {self.object.name}"
        return context


class DepartmentToggleActiveView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        dept = get_object_or_404(Department, pk=pk)
        dept.is_active = not dept.is_active
        dept.save()
        status = "reactivated" if dept.is_active else "deactivated"
        messages.success(request, f"Department '{dept.name}' was successfully {status}.")
        return redirect('admin_department_list')


# Employee CRUD Views

class EmployeeListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'admin_dashboard/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 10

    def get_queryset(self):
        queryset = User.objects.all().order_by('username')
        q = self.request.GET.get('q', '')
        dept_id = self.request.GET.get('department', '')
        
        if q:
            queryset = queryset.filter(
                Q(first_name__icontains=q) | 
                Q(last_name__icontains=q) | 
                Q(username__icontains=q) | 
                Q(employee_id__icontains=q)
            )
        if dept_id:
            queryset = queryset.filter(department_id=dept_id)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['selected_dept'] = self.request.GET.get('department', '')
        context['departments'] = Department.objects.all().order_by('name')
        context['title'] = 'Manage Employees'
        return context


class EmployeeCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = EmployeeAdminForm
    template_name = 'admin_dashboard/employee_form.html'
    success_url = reverse_lazy('admin_employee_list')

    def form_valid(self, form):
        messages.success(self.request, f"Employee account '{form.cleaned_data['username']}' created successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Employee'
        return context


class EmployeeUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    form_class = EmployeeAdminForm
    template_name = 'admin_dashboard/employee_form.html'
    success_url = reverse_lazy('admin_employee_list')

    def form_valid(self, form):
        messages.success(self.request, f"Employee account '{form.cleaned_data['username']}' updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Edit Employee: {self.object.username}"
        return context


class EmployeeToggleActiveView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        employee = get_object_or_404(User, pk=pk)
        if employee == request.user:
            messages.error(request, "You cannot deactivate your own admin account.")
        else:
            employee.is_active = not employee.is_active
            employee.save()
            status = "activated" if employee.is_active else "deactivated"
            messages.success(request, f"Employee account '{employee.username}' was successfully {status}.")
        return redirect('admin_employee_list')
