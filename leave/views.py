from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from .models import LeaveType, LeaveBalance, LeaveRequest
from .forms import LeaveRequestForm, LeaveDecisionForm, LeaveBalanceForm
from users.admin_views import AdminRequiredMixin
from attendance.views import ManagerRequiredMixin

# Employee Views

class LeaveApplyView(LoginRequiredMixin, CreateView):
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'leave/leave_apply.html'
    success_url = reverse_lazy('my_leave_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.employee = self.request.user
        form.instance.status = 'pending'
        messages.success(self.request, "Leave request submitted successfully and is pending approval.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Apply for Leave'
        return context


class MyLeaveListView(LoginRequiredMixin, ListView):
    model = LeaveRequest
    template_name = 'leave/my_leaves.html'
    context_object_name = 'leave_requests'
    paginate_by = 10

    def get_queryset(self):
        return LeaveRequest.objects.filter(employee=self.request.user).select_related('leave_type', 'approved_by').order_by('-applied_on')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = timezone.localdate().year
        context['balances'] = LeaveBalance.objects.filter(
            employee=self.request.user, year=year
        ).select_related('leave_type')
        context['title'] = 'My Leaves'
        context['current_year'] = year
        return context


# Manager Views: Approvals Queue

class PendingApprovalsListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    model = LeaveRequest
    template_name = 'leave/pending_approvals.html'
    context_object_name = 'pending_requests'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        
        # Scoped to department or direct reports, status must be pending
        # Exclude their own requests
        query = Q(employee__manager=user)
        if user.department:
            query = query | Q(employee__department=user.department)
            
        return LeaveRequest.objects.filter(query, status='pending').exclude(
            employee=user
        ).select_related('employee', 'employee__department', 'leave_type').order_by('-applied_on')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Pending Leave Approvals'
        return context


class LeaveDecisionView(LoginRequiredMixin, ManagerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        leave_request = get_object_or_404(LeaveRequest, pk=pk)
        
        # Security check: Ensure manager is authorized for this employee
        user = request.user
        is_subordinate = leave_request.employee.manager == user or (
            user.department and leave_request.employee.department == user.department
        )
        if not is_subordinate and not user.is_superuser and not user.role == 'admin':
            messages.error(request, "You are not authorized to process this leave request.")
            return redirect('pending_approvals_list')

        form = LeaveDecisionForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data['status']
            decision_note = form.cleaned_data['decision_note']
            
            leave_request.status = status
            leave_request.decision_note = decision_note
            leave_request.approved_by = user
            leave_request.save()  # Triggers post_save signals for approval
            
            emp_name = leave_request.employee.get_full_name() or leave_request.employee.username
            messages.success(request, f"Leave request for {emp_name} has been {status}.")
        else:
            messages.error(request, "Invalid decision request parameters.")
            
        return redirect(request.META.get('HTTP_REFERER', 'pending_approvals_list'))


# Admin Views: LeaveType CRUD

class LeaveTypeListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = LeaveType
    template_name = 'leave/admin_leave_types.html'
    context_object_name = 'leave_types'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Manage Leave Types'
        return context


class LeaveTypeCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = LeaveType
    fields = ['name', 'max_days_per_year']
    template_name = 'leave/admin_leave_type_form.html'
    success_url = reverse_lazy('admin_leave_types')

    def form_valid(self, form):
        messages.success(self.request, f"Leave type '{form.cleaned_data['name']}' created successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Leave Type'
        return context


class LeaveTypeUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = LeaveType
    fields = ['name', 'max_days_per_year']
    template_name = 'leave/admin_leave_type_form.html'
    success_url = reverse_lazy('admin_leave_types')

    def form_valid(self, form):
        messages.success(self.request, f"Leave type '{form.cleaned_data['name']}' updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Edit Leave Type: {self.object.name}"
        return context


# Admin Views: LeaveBalance CRUD & Adjustments

class LeaveBalanceListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = LeaveBalance
    template_name = 'leave/admin_balances.html'
    context_object_name = 'balances'
    paginate_by = 15

    def get_queryset(self):
        queryset = LeaveBalance.objects.all().select_related('employee', 'employee__department', 'leave_type').order_by('employee__username')
        
        # Apply filters
        dept_id = self.request.GET.get('department')
        leave_type_id = self.request.GET.get('leave_type')
        q = self.request.GET.get('q', '')
        year = self.request.GET.get('year', str(timezone.localdate().year))
        
        if year:
            queryset = queryset.filter(year=year)
        if dept_id:
            queryset = queryset.filter(employee__department_id=dept_id)
        if leave_type_id:
            queryset = queryset.filter(leave_type_id=leave_type_id)
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
        context['selected_dept'] = self.request.GET.get('department', '')
        context['selected_type'] = self.request.GET.get('leave_type', '')
        context['selected_year'] = self.request.GET.get('year', str(timezone.localdate().year))
        context['q'] = self.request.GET.get('q', '')
        context['departments'] = LeaveBalance.objects.none() # Populate below
        
        # Get helper filter datasets
        from users.models import Department
        context['departments'] = Department.objects.all().order_by('name')
        context['leave_types'] = LeaveType.objects.all().order_by('name')
        context['title'] = 'Manage Employee Leave Balances'
        return context


class LeaveBalanceCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = LeaveBalance
    form_class = LeaveBalanceForm
    template_name = 'leave/admin_balance_form.html'
    success_url = reverse_lazy('admin_balances')

    def form_valid(self, form):
        messages.success(self.request, "Leave balance allocated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Allocate Leave Balance'
        return context


class LeaveBalanceUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = LeaveBalance
    form_class = LeaveBalanceForm
    template_name = 'leave/admin_balance_form.html'
    success_url = reverse_lazy('admin_balances')

    def form_valid(self, form):
        messages.success(self.request, f"Leave balance adjusted for {self.object.employee.username}.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Adjust Balance: {self.object.employee.get_full_name()} ({self.object.leave_type.name})"
        return context
