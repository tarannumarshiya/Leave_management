from django.contrib import admin
from .models import Attendance

class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'check_in_time', 'check_out_time', 'status', 'working_hours']
    list_filter = ['status', 'date', 'employee__department']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name']
    readonly_fields = ['working_hours']

admin.site.register(Attendance, AttendanceAdmin)

