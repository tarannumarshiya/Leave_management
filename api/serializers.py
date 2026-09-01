from rest_framework import serializers
from django.utils import timezone
import datetime

from users.models import User, Department
from attendance.models import Attendance
from leave.models import LeaveType, LeaveBalance, LeaveRequest

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'description', 'is_active']

class UserSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')
    manager_name = serializers.ReadOnlyField(source='manager.get_full_name')

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'role', 'department', 'department_name', 'employee_id', 
            'date_joined_org', 'manager', 'manager_name'
        ]
        read_only_fields = ['id', 'date_joined_org']

class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.ReadOnlyField(source='employee.get_full_name')

    class Meta:
        model = Attendance
        fields = [
            'id', 'employee', 'employee_name', 'date', 
            'check_in_time', 'check_out_time', 'status', 'working_hours'
        ]
        read_only_fields = ['id', 'working_hours']

    def validate(self, data):
        check_in = data.get('check_in_time', getattr(self.instance, 'check_in_time', None))
        check_out = data.get('check_out_time', getattr(self.instance, 'check_out_time', None))
        
        if check_in and check_out:
            if check_out <= check_in:
                raise serializers.ValidationError("Check-out time must be after check-in time.")
        return data

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ['id', 'name', 'max_days_per_year']

class LeaveBalanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.ReadOnlyField(source='employee.get_full_name')
    leave_type_name = serializers.ReadOnlyField(source='leave_type.name')
    remaining_days = serializers.ReadOnlyField()

    class Meta:
        model = LeaveBalance
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 
            'leave_type_name', 'year', 'total_days', 'used_days', 'remaining_days'
        ]
        read_only_fields = ['id', 'remaining_days']

class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.ReadOnlyField(source='employee.get_full_name')
    leave_type_name = serializers.ReadOnlyField(source='leave_type.name')
    approved_by_name = serializers.ReadOnlyField(source='approved_by.get_full_name')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_days = serializers.ReadOnlyField()

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'leave_type_name',
            'start_date', 'end_date', 'reason', 'status', 'status_display',
            'approved_by', 'approved_by_name', 'applied_on', 'decision_note',
            'duration_days'
        ]
        read_only_fields = ['id', 'applied_on', 'duration_days', 'approved_by', 'status']

    def validate(self, data):
        start_date = data.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = data.get('end_date', getattr(self.instance, 'end_date', None))
        leave_type = data.get('leave_type', getattr(self.instance, 'leave_type', None))
        
        # Determine employee (from context request user or serializer data)
        request = self.context.get('request')
        employee = data.get('employee') or (request.user if request else getattr(self.instance, 'employee', None))

        if start_date and end_date:
            if end_date < start_date:
                raise serializers.ValidationError("End date cannot be before start date.")

            if start_date.year != end_date.year:
                raise serializers.ValidationError("Leave requests cannot span across multiple calendar years.")

            if employee and leave_type:
                duration = (end_date - start_date).days + 1
                year = start_date.year
                
                # Fetch/Create balance record
                balance, _ = LeaveBalance.objects.get_or_create(
                    employee=employee,
                    leave_type=leave_type,
                    year=year,
                    defaults={'total_days': leave_type.max_days_per_year, 'used_days': 0}
                )
                
                remaining = balance.remaining_days
                if self.instance and self.instance.pk and self.instance.status == 'approved':
                    remaining += self.instance.duration_days

                if duration > remaining:
                    raise serializers.ValidationError(
                        f"Insufficient leave balance. Requested {duration} days, but only {remaining} days remain."
                    )

                # Overlap validation
                overlap_query = LeaveRequest.objects.filter(
                    employee=employee,
                    status__in=['approved', 'pending'],
                    start_date__lte=end_date,
                    end_date__gte=start_date
                )
                if self.instance and self.instance.pk:
                    overlap_query = overlap_query.exclude(pk=self.instance.pk)

                if overlap_query.exists():
                    raise serializers.ValidationError("Leave request overlaps with an existing pending or approved request.")

        return data
