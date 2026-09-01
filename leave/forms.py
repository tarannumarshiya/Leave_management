from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
import datetime

from .models import LeaveRequest, LeaveBalance, LeaveType
from users.models import User

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Reason for leave...'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'leave_type':
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
                
        # Limit leave types to active ones
        self.fields['leave_type'].queryset = LeaveType.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        leave_type = cleaned_data.get('leave_type')

        if not self.user:
            raise ValidationError("User context is required to validate leave balance.")

        if start_date and end_date and leave_type:
            # 1. Date chronological check
            if end_date < start_date:
                raise ValidationError("End date cannot be before start date.")
                
            # 2. Year check: start and end must be in same year for ease of balance tracking
            if start_date.year != end_date.year:
                raise ValidationError("Leave requests cannot cross calendar years. Please submit separate requests for each year.")

            # 3. Balance validation
            duration = (end_date - start_date).days + 1
            year = start_date.year
            
            # Fetch/Create the balance record for this employee/type/year
            balance, _ = LeaveBalance.objects.get_or_create(
                employee=self.user,
                leave_type=leave_type,
                year=year,
                defaults={'total_days': leave_type.max_days_per_year, 'used_days': 0}
            )
            
            # If editing an existing request, we exclude its days if it was already marked as approved
            # (although in our design, editing an approved request shouldn't happen, but let's be robust)
            remaining = balance.remaining_days
            if self.instance and self.instance.pk and self.instance.status == 'approved':
                # The days are already counted in used_days, so add them back for checking
                remaining += self.instance.duration_days

            if duration > remaining:
                raise ValidationError(
                    f"Insufficient leave balance. You requested {duration} days, but only have {remaining} days remaining."
                )

            # 4. Overlap validation (cannot overlap with any approved or pending requests)
            # Approved leaves or other pending requests
            overlap_query = LeaveRequest.objects.filter(
                employee=self.user,
                status__in=['approved', 'pending'],
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            
            if self.instance and self.instance.pk:
                overlap_query = overlap_query.exclude(pk=self.instance.pk)
                
            if overlap_query.exists():
                raise ValidationError("This request overlaps with an existing pending or approved leave request.")

        return cleaned_data


class LeaveDecisionForm(forms.Form):
    status = forms.ChoiceField(
        choices=[('approved', 'Approve'), ('rejected', 'Reject')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    decision_note = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional decision note...'}),
        required=False
    )


class LeaveBalanceForm(forms.ModelForm):
    class Meta:
        model = LeaveBalance
        fields = ['employee', 'leave_type', 'year', 'total_days', 'used_days']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name in ['employee', 'leave_type']:
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
                
        # Limit employees to active ones
        self.fields['employee'].queryset = User.objects.filter(is_active=True)
