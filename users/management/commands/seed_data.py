from django.core.management.base import BaseCommand
from users.models import User, Department
from datetime import date
from django.utils import timezone

class Command(BaseCommand):
    help = 'Seed the database with initial departments and test accounts for employee, manager, and admin'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Seeding initial data...'))

        # Create Departments
        depts_data = [
            {'name': 'Engineering', 'code': 'ENG', 'description': 'Software development, QA, and operations.'},
            {'name': 'Human Resources', 'code': 'HR', 'description': 'People management, recruitment, and benefits.'},
            {'name': 'Sales & Marketing', 'code': 'MKT', 'description': 'Customer acquisition and branding.'},
        ]
        
        departments = {}
        for d_info in depts_data:
            dept, created = Department.objects.get_or_create(
                code=d_info['code'],
                defaults={
                    'name': d_info['name'],
                    'description': d_info['description'],
                    'is_active': True
                }
            )
            # Update name and description if already exists
            if not created:
                dept.name = d_info['name']
                dept.description = d_info['description']
                dept.save()
            departments[d_info['name']] = dept
            if created:
                self.stdout.write(self.style.SUCCESS(f"Department '{dept.name}' ({dept.code}) created."))
            else:
                self.stdout.write(f"Department '{dept.name}' ({dept.code}) already exists.")

        # Create Test Users (First pass: without manager foreign key)
        users_data = [
            {
                'username': 'employee',
                'email': 'employee@example.com',
                'password': 'password123',
                'first_name': 'Emily',
                'last_name': 'Employee',
                'role': 'employee',
                'department': departments['Engineering'],
                'employee_id': 'EMP-001',
                'date_joined_org': date(2025, 1, 15),
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'manager',
                'email': 'manager@example.com',
                'password': 'password123',
                'first_name': 'Marcus',
                'last_name': 'Manager',
                'role': 'manager',
                'department': departments['Engineering'],
                'employee_id': 'EMP-002',
                'date_joined_org': date(2024, 6, 1),
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'password': 'password123',
                'first_name': 'Alice',
                'last_name': 'Admin',
                'role': 'admin',
                'department': departments['Human Resources'],
                'employee_id': 'EMP-003',
                'date_joined_org': date(2023, 10, 1),
                'is_staff': True,
                'is_superuser': True,
            }
        ]

        created_users = {}
        for u_info in users_data:
            username = u_info['username']
            password = u_info.pop('password')
            dept = u_info.pop('department')
            
            user = User.objects.filter(username=username).first()
            if not user:
                user = User.objects.create_user(
                    username=username,
                    email=u_info['email'],
                    first_name=u_info['first_name'],
                    last_name=u_info['last_name'],
                    role=u_info['role'],
                    department=dept,
                    employee_id=u_info['employee_id'],
                    date_joined_org=u_info['date_joined_org'],
                    is_staff=u_info['is_staff'],
                    is_superuser=u_info['is_superuser']
                )
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"User '{username}' created with password 'password123'."))
            else:
                user.email = u_info['email']
                user.first_name = u_info['first_name']
                user.last_name = u_info['last_name']
                user.role = u_info['role']
                user.department = dept
                user.employee_id = u_info['employee_id']
                user.date_joined_org = u_info['date_joined_org']
                user.is_staff = u_info['is_staff']
                user.is_superuser = u_info['is_superuser']
                user.set_password(password)
                user.save()
                self.stdout.write(f"User '{username}' already exists. Password reset to 'password123'.")
            created_users[username] = user

        # Second pass: Associate managers
        self.stdout.write('Associating reporting managers...')
        
        # Emily Employee reports to Marcus Manager
        emp_user = created_users['employee']
        emp_user.manager = created_users['manager']
        emp_user.save()
        self.stdout.write("Emily Employee's manager set to Marcus Manager.")

        # Marcus Manager reports to Alice Admin
        mgr_user = created_users['manager']
        mgr_user.manager = created_users['admin']
        mgr_user.save()
        self.stdout.write("Marcus Manager's manager set to Alice Admin.")

        # Seed Attendance Records
        from attendance.models import Attendance
        import datetime
        
        self.stdout.write('Seeding attendance records...')
        today = timezone.localdate()
        
        # Seed records for last 5 days
        for i in range(1, 6):
            check_date = today - datetime.timedelta(days=i)
            
            # Employee: 9:00 AM to 5:00 PM (8 hrs)
            Attendance.objects.get_or_create(
                employee=created_users['employee'],
                date=check_date,
                defaults={
                    'check_in_time': datetime.time(9, 0),
                    'check_out_time': datetime.time(17, 0),
                    'status': 'present'
                }
            )
            
            # Manager: 8:30 AM to 5:30 PM (9 hrs)
            Attendance.objects.get_or_create(
                employee=created_users['manager'],
                date=check_date,
                defaults={
                    'check_in_time': datetime.time(8, 30),
                    'check_out_time': datetime.time(17, 30),
                    'status': 'present'
                }
            )
            
        self.stdout.write(self.style.SUCCESS("Attendance records seeded for Emily Employee and Marcus Manager."))

        # Seed Leave Types
        from leave.models import LeaveType, LeaveBalance, LeaveRequest
        self.stdout.write('Seeding leave types...')
        annual_leave, _ = LeaveType.objects.get_or_create(name='Annual Leave', defaults={'max_days_per_year': 15})
        sick_leave, _ = LeaveType.objects.get_or_create(name='Sick Leave', defaults={'max_days_per_year': 10})
        unpaid_leave, _ = LeaveType.objects.get_or_create(name='Unpaid Leave', defaults={'max_days_per_year': 30})
        
        self.stdout.write('Seeding employee leave balances...')
        current_year = today.year
        # Seed balances
        for username, user in created_users.items():
            LeaveBalance.objects.get_or_create(
                employee=user,
                leave_type=annual_leave,
                year=current_year,
                defaults={'total_days': 15, 'used_days': 0}
            )
            LeaveBalance.objects.get_or_create(
                employee=user,
                leave_type=sick_leave,
                year=current_year,
                defaults={'total_days': 10, 'used_days': 0}
            )

        # Seed a pending leave request from employee
        self.stdout.write('Seeding a pending leave request...')
        LeaveRequest.objects.get_or_create(
            employee=created_users['employee'],
            leave_type=annual_leave,
            start_date=today + datetime.timedelta(days=5),
            end_date=today + datetime.timedelta(days=7),
            defaults={
                'reason': 'Family trip to Yosemite.',
                'status': 'pending'
            }
        )
        self.stdout.write(self.style.SUCCESS("Leave configurations and pending requests seeded."))
        self.stdout.write(self.style.SUCCESS('Successfully seeded database!'))


