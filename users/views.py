from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, TemplateView, View
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied

from .models import User, Department
from .forms import CustomUserCreationForm

class RoleRequiredMixin(UserPassesTestMixin):
    """
    Mixin to restrict view access based on user role.
    """
    allowed_roles = []

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        # Superuser and admin role are always allowed
        if self.request.user.is_superuser or self.request.user.role == 'admin':
            return True
        return self.request.user.role in self.allowed_roles

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You do not have permission to view this page.")
        return redirect('login')

class RegisterView(CreateView):
    """
    Custom view for User registration.
    """
    model = User
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('dashboard_redirect')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard_redirect')
        return super().dispatch(request, *args, **kwargs)

class DashboardRedirectView(LoginRequiredMixin, View):
    """
    Redirects user to their role-specific dashboard.
    """
    def get(self, request, *args, **kwargs):
        role = request.user.role
        if request.user.is_superuser or role == 'admin':
            return redirect('admin_dashboard')
        elif role == 'manager':
            return redirect('manager_dashboard')
        else:
            return redirect('employee_dashboard')

class EmployeeDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    """
    Employee Dashboard View.
    """
    template_name = 'dashboards/employee.html'
    allowed_roles = ['employee']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Employee Dashboard'
        from attendance.models import Attendance
        from leave.models import LeaveRequest, LeaveBalance
        from django.utils import timezone
        import json
        today = timezone.localdate()

        context['today_attendance'] = Attendance.objects.filter(
            employee=self.request.user, date=today
        ).first()
        context['recent_leaves'] = LeaveRequest.objects.filter(
            employee=self.request.user
        ).select_related('leave_type').order_by('-applied_on')[:5]
        
        balances_qs = LeaveBalance.objects.filter(
            employee=self.request.user, year=today.year
        ).select_related('leave_type')
        context['balances'] = balances_qs
        
        balances_list = list(balances_qs)
        balance_labels = [b.leave_type.name for b in balances_list]
        balance_remaining = [b.remaining_days for b in balances_list]
        balance_used = [b.used_days for b in balances_list]
        
        context['balance_labels'] = balance_labels
        context['balance_remaining'] = balance_remaining
        context['balance_used'] = balance_used
        
        return context

class ManagerDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    """
    Manager Dashboard View.
    """
    template_name = 'dashboards/manager.html'
    allowed_roles = ['manager']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Manager Dashboard'
        from attendance.models import Attendance
        from leave.models import LeaveRequest
        from users.models import User
        from django.utils import timezone
        from django.db.models import Q

        today = timezone.localdate()
        user = self.request.user

        context['today_attendance'] = Attendance.objects.filter(
            employee=user, date=today
        ).first()

        sub_query = Q(manager=user)
        if user.department:
            sub_query = sub_query | Q(department=user.department)

        team_members = User.objects.filter(sub_query).exclude(pk=user.pk)
        context['team_total_count'] = team_members.count()

        pending_qs = LeaveRequest.objects.filter(
            employee__in=team_members, status='pending'
        ).select_related('employee', 'leave_type').order_by('-applied_on')
        context['pending_leaves'] = pending_qs[:5]
        context['pending_count'] = pending_qs.count()

        team_today_att = Attendance.objects.filter(
            employee__in=team_members, date=today
        ).select_related('employee')

        context['team_present_count'] = team_today_att.filter(status__in=['present', 'half-day']).count()
        context['team_on_leave_today'] = team_today_att.filter(status='leave')

        # Construct team attendance list mapping each member to their attendance record
        att_map = {att.employee_id: att for att in team_today_att}
        team_attendance_list = []
        for member in team_members:
            team_attendance_list.append({
                'employee': member,
                'attendance': att_map.get(member.id)
            })
        context['team_attendance_today'] = team_attendance_list

        # Calculate attendance status counts for Chart.js
        present_count = team_today_att.filter(status='present').count()
        half_day_count = team_today_att.filter(status='half-day').count()
        leave_count = team_today_att.filter(status='leave').count()
        absent_count = team_today_att.filter(status='absent').count()
        untracked_count = max(0, team_members.count() - team_today_att.count())

        attendance_labels = ['Present', 'Half Day', 'On Leave', 'Absent', 'Not Checked In']
        attendance_counts = [present_count, half_day_count, leave_count, absent_count, untracked_count]

        context['attendance_labels'] = attendance_labels
        context['attendance_counts'] = attendance_counts

        return context

class AdminDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    """
    Admin Dashboard View.
    """
    template_name = 'dashboards/admin.html'
    allowed_roles = ['admin']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Admin Dashboard'
        from attendance.models import Attendance
        from leave.models import LeaveRequest
        from users.models import Department, User
        from django.utils import timezone

        today = timezone.localdate()

        org_headcount = User.objects.filter(is_active=True).count()
        context['org_headcount'] = org_headcount
        context['total_users'] = org_headcount
        context['total_departments'] = Department.objects.count()

        present_today = Attendance.objects.filter(date=today, status__in=['present', 'half-day']).count()
        attendance_pct = round((present_today / org_headcount * 100), 1) if org_headcount > 0 else 0.0
        context['attendance_pct_today'] = attendance_pct

        pending_count = LeaveRequest.objects.filter(status='pending').count()
        context['pending_leaves_count'] = pending_count
        context['pending_count'] = pending_count

        depts = Department.objects.all()
        dept_labels = [d.name for d in depts]
        dept_counts = [d.users.filter(is_active=True).count() for d in depts]

        context['dept_labels'] = dept_labels
        context['dept_counts'] = dept_counts

        status_labels = ['Approved', 'Pending', 'Rejected']
        status_counts = [
            LeaveRequest.objects.filter(status='approved').count(),
            LeaveRequest.objects.filter(status='pending').count(),
            LeaveRequest.objects.filter(status='rejected').count(),
        ]
        context['leave_status_labels'] = status_labels
        context['leave_status_counts'] = status_counts

        return context

