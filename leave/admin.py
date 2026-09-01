from django.contrib import admin
from .models import LeaveType, LeaveBalance, LeaveRequest

class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'max_days_per_year']

class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'year', 'total_days', 'used_days', 'remaining_days']
    list_filter = ['year', 'leave_type', 'employee__department']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name']

class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'status', 'duration_days', 'applied_on']
    list_filter = ['status', 'leave_type', 'start_date']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name']
    readonly_fields = ['applied_on', 'is_deducted']

admin.site.register(LeaveType, LeaveTypeAdmin)
admin.site.register(LeaveBalance, LeaveBalanceAdmin)
admin.site.register(LeaveRequest, LeaveRequestAdmin)

