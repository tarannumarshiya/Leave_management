# LeaveFlow - Enterprise Leave & Attendance Management System

[![Django](https://img.shields.io/badge/Django-5.0.14-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-5432-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![REST API](https://img.shields.io/badge/Django_REST_Framework-3.17-red?style=for-the-badge)](https://www.django-rest-framework.org/)

**LeaveFlow** is a modern, full-stack human resource management platform built with Django, PostgreSQL, and Bootstrap 5. It streamlines workforce attendance tracking, annual leave allocations, manager approval workflows, organizational audits, and RESTful API integrations.

---

## 🌟 Key Features

- **Public Landing Page**: Engaging product showcase featuring live UI mockups, 4-metric KPI strip, role breakdowns, and quick entry points.
- **1-Click Attendance**: One-click check-in and check-out with automated working-hour computation and zero manual calculation discrepancies.
- **Yearly Leave Quota Tracking**: Dynamic leave types (Casual, Sick, Annual, Unpaid) with year-by-year balance allocation and validation against remaining days.
- **Manager Approval Queues**: Role-scoped approval queues for department heads and line managers with custom feedback notes.
- **Automated Post-Save Signals**:
  - Auto-deducts approved days from employee quota balances.
  - Automatically records `status='leave'` on the Attendance table for the full approved date range.
  - Dispatches automated email notifications to managers (on application) and employees (on decision).
- **Interactive Dashboards**: Role-specific dashboards featuring Chart.js visualizations for team attendance splits, department distributions, and approval rates.
- **Org-Wide Auditing & CSV Export**: Searchable and filterable attendance archives with single-click CSV export ready for payroll.
- **Show/Hide Password Toggles**: Accessible password visibility eye icons on Login and Registration forms.
- **Full REST API with JWT**: Complete Django REST Framework API with OpenAPI/Swagger schema documentation via `drf-spectacular`.

---

## 👥 Role-Based Access Control (RBAC)

The system enforces strict permission boundaries across three distinct user roles:

| Role | Default Username | Default Password | Capabilities & Scope |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `password123` | Full org governance, Department CRUD, User administration, Leave Type & Balance management, Org Attendance audits, CSV exports, Django Admin access. |
| **Manager** | `manager` | `password123` | Department team attendance oversight, pending leave approvals queue with decision notes, automated email alerts for direct reports. |
| **Employee** | `employee` | `password123` | 1-Click daily check-in / check-out, leave request submission, personal leave quota balances, attendance history log. |

---

## 🔄 End-to-End System Workflow

```mermaid
flowchart TD
    A([User Visits /]) --> B{Authenticated?}
    B -->|No| C[Public Landing Page / Login / Register]
    B -->|Yes| D[Dashboard Redirect View]
    
    D -->|Role: Employee| E[Employee Dashboard]
    D -->|Role: Manager| F[Manager Dashboard]
    D -->|Role: Admin| G[Admin Dashboard]

    subgraph Employee Workflow
        E --> AttIn[Daily Check-In / Check-Out]
        AttIn --> CalcHours[Auto-calculate Working Hours]
        E --> ApplyLeave[Submit Leave Application]
    end

    subgraph Manager Workflow
        ApplyLeave --> AlertMgr[Email Signal to Manager]
        AlertMgr --> MgrQueue[Review in Approvals Queue]
        MgrQueue --> Decision{Approve or Reject?}
    end

    subgraph Automation on Approval
        Decision -->|Approved| Deduct[Deduct LeaveBalance.used_days]
        Deduct --> SyncAtt[Auto-Create Attendance records with status='leave']
        SyncAtt --> NotifyEmp[Email Signal to Employee]
        Decision -->|Rejected| NotifyReject[Email Rejection Note to Employee]
    end

    subgraph Admin Governance
        G --> UserMgmt[User & Hierarchy CRUD]
        G --> DeptMgmt[Department CRUD & Toggle Active]
        G --> QuotaMgmt[Configure Leave Types & Balances]
        G --> CSVExport[Filter Attendance & Export CSV]
    end
```

### Detailed Lifecycle Steps

1. **Authentication & Dynamic Redirection**:
   - When a user logs in, `DashboardRedirectView` detects their assigned role (`employee`, `manager`, or `admin`) and redirects them to their tailored dashboard.
2. **Attendance Tracking**:
   - Employees check in upon arrival (`check_in_time`) and check out when leaving (`check_out_time`).
   - The model automatically computes `working_hours = round(diff_seconds / 3600, 2)` upon saving.
3. **Leave Request Validation**:
   - `LeaveRequestForm` validates that `start_date <= end_date`, leaves are within the same calendar year, the employee has sufficient `remaining_days`, and dates do not conflict with existing approved or pending requests.
4. **Approval & Automated Side-Effects**:
   - When a manager approves a request:
     1. The `post_save` signal increments `LeaveBalance.used_days`.
     2. `Attendance` records for every date within `[start_date, end_date]` are automatically generated/updated with `status='leave'`.
     3. An email confirmation containing the decision note is sent to the employee.
5. **Administrative Audits**:
   - HR Admins filter organization-wide records by department, status, date range, or employee name, and download formatted `.csv` reports for payroll processing.

---

## 🗄️ Database & pgAdmin Configuration

LeaveFlow uses **PostgreSQL** as its persistent relational database.

### 1. Database Connection Parameters
- **Host**: `localhost` (or `127.0.0.1`)
- **Port**: `5432`
- **Database Name**: `leave_attendance_db`
- **Username**: `postgres`
- **Password**: `admin123` (configured in your `.env` file)
- **Connection URL**: `postgresql://postgres:admin123@localhost:5432/leave_attendance_db`

---

### 2. How to Connect in pgAdmin 4

Follow these steps to view and query your database tables visually in pgAdmin:

1. **Open pgAdmin 4** on your machine.
2. In the left sidebar (*Object Explorer*), right-click on **Servers** $\rightarrow$ select **Register** $\rightarrow$ **Server...**
3. In the **General** tab:
   - **Name**: `LeaveFlow DB` (or any display name).
4. In the **Connection** tab, enter:
   - **Host name/address**: `localhost`
   - **Port**: `5432`
   - **Maintenance database**: `leave_attendance_db`
   - **Username**: `postgres`
   - **Password**: `admin123`
   - Check the **Save Password** checkbox.
5. Click **Save**.
6. **Browse Tables**:
   - Expand `Servers` $\rightarrow$ `LeaveFlow DB` $\rightarrow$ `Databases` $\rightarrow$ `leave_attendance_db` $\rightarrow$ `Schemas` $\rightarrow$ `public` $\rightarrow$ `Tables`.
   - You will see all system tables:
     - `users_user` (Employees, managers, admins, reporting hierarchy)
     - `users_department` (Departments and active flags)
     - `attendance_attendance` (Daily timestamps, status, hours)
     - `leave_leavetype` (Annual, Sick, Casual leave definitions)
     - `leave_leavebalance` (Yearly total days vs used days)
     - `leave_leaverequest` (Application dates, reason, status, decision note)
7. **View / Query Data**:
   - Right-click any table (e.g., `attendance_attendance`) $\rightarrow$ select **View/Edit Data** $\rightarrow$ **All Rows**.
   - Or open the **Query Tool** and run SQL queries:
     ```sql
     SELECT u.username, d.name AS department, a.date, a.status, a.working_hours
     FROM attendance_attendance a
     JOIN users_user u ON a.employee_id = u.id
     LEFT JOIN users_department d ON u.department_id = d.id
     ORDER BY a.date DESC;
     ```

---

## 🚀 Local Development Setup

### 1. Prerequisites
- **Python 3.12+**
- **PostgreSQL 14+** running locally on port `5432`

### 2. Clone & Environment Setup
```powershell
# Navigate to the project directory
cd c:\Users\ABC\Desktop\Leave_management

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1
```

*(If script execution is disabled in PowerShell, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create or verify the `.env` file in the root directory:
```env
DEBUG=True
SECRET_KEY=django-insecure-your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://postgres:admin123@localhost:5432/leave_attendance_db
```

### 5. Apply Migrations & Seed Initial Data
```powershell
# Apply database schema migrations
python manage.py migrate

# Seed departments, test accounts (admin, manager, employee), and sample logs
python manage.py seed_data
```

### 6. Start Development Server
```powershell
python manage.py runserver
```
Visit **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

---

## 📡 REST API Reference

The project includes a full REST API layer available under `/api/` with Token & Session Authentication:

| Endpoint | Method | Allowed Roles | Description |
| :--- | :--- | :--- | :--- |
| `/api/token/` | `POST` | Public | Obtain JWT Access and Refresh Tokens |
| `/api/token/refresh/` | `POST` | Public | Refresh expired JWT access token |
| `/api/departments/` | `GET, POST, PUT, DELETE` | Admin (Write) / All (Read) | Department CRUD |
| `/api/users/` | `GET` | Role-Scoped | List user profiles and hierarchy |
| `/api/attendance/` | `GET, POST, PUT` | Owner / Manager / Admin | View and create daily attendance |
| `/api/leave-types/` | `GET, POST, PUT, DELETE` | Admin (Write) / All (Read) | Manage leave types and annual quotas |
| `/api/leave-balances/` | `GET, POST, PUT` | Owner / Manager / Admin | Manage employee yearly leave balances |
| `/api/leave-requests/` | `GET, POST` | Owner / Manager / Admin | Submit and view leave applications |
| `/api/leave-requests/{id}/approve/` | `POST` | Manager of Employee / Admin | Approve pending leave request |
| `/api/leave-requests/{id}/reject/` | `POST` | Manager of Employee / Admin | Reject pending leave request |

### Interactive API Documentation
- **Swagger UI**: [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- **Raw OpenAPI Schema**: [http://127.0.0.1:8000/api/schema/](http://127.0.0.1:8000/api/schema/)

---

## 🧪 Running Automated Tests

Run the complete test suite across all apps (`users`, `attendance`, `leave`, `api`):

```powershell
python manage.py test
```

All 19 automated test cases will run against an isolated test database and validate model constraints, form validations, role permissions, signals, and API endpoints.

---

## 📂 Project Directory Structure

```text
Leave_management/
├── api/                             # Django REST Framework ViewSets & Serializers
│   ├── permissions.py               # Custom RBAC permissions (IsAdmin, IsOwnerOrManager, etc.)
│   ├── serializers.py               # DRF model serializers with validation
│   ├── urls.py                      # REST route definitions
│   └── views.py                     # API ViewSets & custom actions (approve/reject)
├── attendance/                      # Daily Clock-In / Check-Out App
│   ├── models.py                    # Attendance model with working_hours auto-calc
│   ├── urls.py                      # URLs for personal, team, and org attendance
│   └── views.py                     # CheckInOutView, TeamAttendanceView, ExportCSVView
├── core/                            # Public & General Views
│   ├── urls.py                      # Public landing page route (/)
│   └── views.py                     # HomeView (renders landing page)
├── leave/                           # Leave Management & Approvals App
│   ├── forms.py                     # LeaveRequestForm, LeaveDecisionForm, LeaveBalanceForm
│   ├── models.py                    # LeaveType, LeaveBalance, LeaveRequest
│   ├── signals.py                   # Pre/post-save signals (balance deduct & attendance sync)
│   ├── urls.py                      # Leave application, approval queues, admin balance URLs
│   └── views.py                     # LeaveApplyView, PendingApprovalsListView, DecisionView
├── leave_attendance_system/         # Project Configuration Root
│   ├── settings/                    # Modular settings (base.py, dev.py, prod.py)
│   ├── urls.py                      # Global URL router
│   └── wsgi.py                      # WSGI entry point
├── templates/                       # HTML Templates
│   ├── admin_dashboard/             # Admin management templates (departments, employees)
│   ├── attendance/                  # Attendance views (my, team, org attendance logs)
│   ├── dashboards/                  # Role-specific dashboards (employee, manager, admin)
│   ├── leave/                       # Leave forms, my leaves, pending approvals queue
│   ├── registration/                # Login (with eye toggle), register, logged_out
│   ├── base.html                    # Base layout with navbar, alerts, footer
│   └── home.html                    # Public product landing page
├── users/                           # Custom User & Department App
│   ├── admin_views.py               # Admin Department & Employee CRUD views
│   ├── forms.py                     # CustomUserCreationForm, EmployeeAdminForm
│   ├── management/commands/         # seed_data management command
│   ├── models.py                    # User (AbstractUser with roles) & Department models
│   └── views.py                     # DashboardRedirectView, role-specific views
├── static/                          # CSS stylesheets, JavaScript files, assets
├── manage.py                        # Django CLI entrypoint
├── requirements.txt                 # Python package dependencies
└── README.md                        # Project documentation
```

---

## 📄 License
This project is developed for internal organizational management and educational demonstration.
