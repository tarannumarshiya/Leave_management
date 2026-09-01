import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Q

from django.core.exceptions import PermissionDenied
from .models import Attendance
from users.models import Department
from users.admin_views import AdminRequiredMixin

class ManagerRequiredMixin(UserPassesTestMixin):
    """
    Restricts access to only manager and admin users.
    """
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.role in ['manager', 'admin'] or self.request.user.is_superuser
        )

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You do not have permission to view team attendance details.")
        return super().handle_no_permission()


# Attendance Check-In / Check-Out View

class AttendanceCheckInOutView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        today = timezone.localdate()
        now_time = timezone.localtime().time()
        
        # Get or create record for today
        attendance, created = Attendance.objects.get_or_create(
            employee=request.user,
            date=today,
            defaults={'status': 'present'}
        )
        
        action = request.POST.get('action')
        
        if action == 'check_in':
            if not created and attendance.check_in_time:
                messages.warning(request, "You have already checked in today.")
            else:
                attendance.check_in_time = now_time
                attendance.status = 'present'
                attendance.save()
                messages.success(request, f"Successfully checked in at {now_time.strftime('%I:%M %p')}.")
        
        elif action == 'check_out':
            if not attendance.check_in_time:
                messages.error(request, "You must check in first before checking out.")
            elif attendance.check_out_time:
                messages.warning(request, "You have already checked out today.")
            else:
                attendance.check_out_time = now_time
                attendance.save()
                messages.success(
                    request, 
                    f"Successfully checked out at {now_time.strftime('%I:%M %p')}. "
                    f"Total working hours: {attendance.working_hours} hours."
                )
                
        return redirect(request.META.get('HTTP_REFERER', 'dashboard_redirect'))


# Employee: My Attendance History View

class MyAttendanceListView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = 'attendance/my_attendance.html'
    context_object_name = 'attendances'
    paginate_by = 10

    def get_queryset(self):
        queryset = Attendance.objects.filter(employee=self.request.user).order_by('-date')
        
        # Apply date filters
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['title'] = 'My Attendance Log'
        return context


# Manager: Team Attendance View

class TeamAttendanceListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    model = Attendance
    template_name = 'attendance/team_attendance.html'
    context_object_name = 'attendances'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if not user.department:
            return Attendance.objects.none()
            
        # Get team records
        queryset = Attendance.objects.filter(
            employee__department=user.department
        ).select_related('employee', 'employee__department').order_by('-date')
        
        # Apply filters
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        status = self.request.GET.get('status')
        q = self.request.GET.get('q', '')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if status:
            queryset = queryset.filter(status=status)
        if q:
            queryset = queryset.filter(
                Q(employee__first_name__icontains=q) | 
                Q(employee__last_name__icontains=q) | 
                Q(employee__username__icontains=q) |
                Q(employee__employee_id__icontains=q)
            )
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['status'] = self.request.GET.get('status', '')
        context['q'] = self.request.GET.get('q', '')
        context['title'] = f"Team Attendance - {self.request.user.department.name if self.request.user.department else 'No Department'}"
        return context


# Admin: Org-wide Attendance View

class OrgAttendanceListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Attendance
    template_name = 'attendance/org_attendance.html'
    context_object_name = 'attendances'
    paginate_by = 15

    def get_queryset(self):
        queryset = Attendance.objects.all().select_related('employee', 'employee__department').order_by('-date')
        
        # Apply filters
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        status = self.request.GET.get('status')
        dept_id = self.request.GET.get('department')
        q = self.request.GET.get('q', '')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if status:
            queryset = queryset.filter(status=status)
        if dept_id:
            queryset = queryset.filter(employee__department_id=dept_id)
        if q:
            queryset = queryset.filter(
                Q(employee__first_name__icontains=q) | 
                Q(employee__last_name__icontains=q) | 
                Q(employee__username__icontains=q) |
                Q(employee__employee_id__icontains=q)
            )
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['status'] = self.request.GET.get('status', '')
        context['selected_dept'] = self.request.GET.get('department', '')
        context['q'] = self.request.GET.get('q', '')
        context['departments'] = Department.objects.all().order_by('name')
        context['title'] = 'Organization Attendance Log'
        return context


# Admin: CSV Export View

class ExportAttendanceCSVView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        queryset = Attendance.objects.all().select_related('employee', 'employee__department').order_by('-date')
        
        # Apply the exact same filters as list view
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        status = request.GET.get('status')
        dept_id = request.GET.get('department')
        q = request.GET.get('q')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if status:
            queryset = queryset.filter(status=status)
        if dept_id:
            queryset = queryset.filter(employee__department_id=dept_id)
        if q:
            queryset = queryset.filter(
                Q(employee__first_name__icontains=q) | 
                Q(employee__last_name__icontains=q) | 
                Q(employee__username__icontains=q) |
                Q(employee__employee_id__icontains=q)
            )
            
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="attendance_export_{timezone.localdate()}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Date', 'Employee ID', 'Username', 'Full Name', 'Department', 'Check-In', 'Check-Out', 'Status', 'Working Hours'])
        
        for record in queryset:
            writer.writerow([
                record.date,
                record.employee.employee_id or '—',
                record.employee.username,
                record.employee.get_full_name() or record.employee.username,
                record.employee.department.name if record.employee.department else 'Unassigned',
                record.check_in_time.strftime('%I:%M %p') if record.check_in_time else '—',
                record.check_out_time.strftime('%I:%M %p') if record.check_out_time else '—',
                record.get_status_display(),
                record.working_hours
            ])
            
        return response
