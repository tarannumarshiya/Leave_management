from django.urls import path
from .views import (
    LeaveApplyView,
    MyLeaveListView,
    PendingApprovalsListView,
    LeaveDecisionView,
    LeaveTypeListView,
    LeaveTypeCreateView,
    LeaveTypeUpdateView,
    LeaveBalanceListView,
    LeaveBalanceCreateView,
    LeaveBalanceUpdateView
)

urlpatterns = [
    path('apply/', LeaveApplyView.as_view(), name='leave_apply'),
    path('my/', MyLeaveListView.as_view(), name='my_leave_list'),
    path('pending/', PendingApprovalsListView.as_view(), name='pending_approvals_list'),
    path('decision/<int:pk>/', LeaveDecisionView.as_view(), name='leave_decision'),
    
    # Admin URLs
    path('admin/types/', LeaveTypeListView.as_view(), name='admin_leave_types'),
    path('admin/types/create/', LeaveTypeCreateView.as_view(), name='admin_leave_type_create'),
    path('admin/types/update/<int:pk>/', LeaveTypeUpdateView.as_view(), name='admin_leave_type_update'),
    
    path('admin/balances/', LeaveBalanceListView.as_view(), name='admin_balances'),
    path('admin/balances/create/', LeaveBalanceCreateView.as_view(), name='admin_balance_create'),
    path('admin/balances/update/<int:pk>/', LeaveBalanceUpdateView.as_view(), name='admin_balance_update'),
]
