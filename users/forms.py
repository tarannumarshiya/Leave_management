from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, Department

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'department')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap styling to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name in ['role', 'department']:
                field.widget.attrs['class'] = 'form-select'

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'is_active', 'is_staff')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap styling to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name in ['role', 'department']:
                field.widget.attrs['class'] = 'form-select'


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'is_active':
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class EmployeeAdminForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        help_text="Leave blank if editing and password should not change."
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'role', 
            'department', 'employee_id', 'date_joined_org', 'manager', 'is_active'
        ]
        widgets = {
            'date_joined_org': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Modify password requirement for update vs creation
        if self.instance and self.instance.pk:
            self.fields['password'].required = False
            self.fields['password'].help_text = "Leave blank if you don't want to change the password."
        else:
            self.fields['password'].required = True
            self.fields['password'].help_text = "Password is required for new accounts."

        for field_name, field in self.fields.items():
            if field_name == 'is_active':
                field.widget.attrs['class'] = 'form-check-input'
            elif field_name in ['role', 'department', 'manager']:
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
                
        # Limit manager choices to only managers and admins
        self.fields['manager'].queryset = User.objects.filter(role__in=['manager', 'admin'])

    def clean(self):
        cleaned_data = super().clean()
        manager = cleaned_data.get('manager')
        if self.instance and manager == self.instance:
            raise forms.ValidationError("An employee cannot be their own manager.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user
