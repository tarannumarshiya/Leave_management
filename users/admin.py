from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Department
from .forms import CustomUserCreationForm, CustomUserChangeForm

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    search_fields = ['name', 'code']

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ['username', 'email', 'role', 'department', 'employee_id', 'is_active']
    list_filter = ['role', 'department', 'is_active']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Employee Profile Details', {'fields': ('role', 'department', 'employee_id', 'date_joined_org', 'manager')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Employee Profile Details', {'fields': ('role', 'department', 'employee_id', 'date_joined_org', 'manager', 'email', 'first_name', 'last_name')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Department, DepartmentAdmin)


