from django.urls import path
from .views import (
    AttendanceCheckInOutView,
    MyAttendanceListView,
    TeamAttendanceListView,
    OrgAttendanceListView,
    ExportAttendanceCSVView
)

urlpatterns = [
    path('check-in-out/', AttendanceCheckInOutView.as_view(), name='attendance_check_in_out'),
    path('my/', MyAttendanceListView.as_view(), name='my_attendance_list'),
    path('team/', TeamAttendanceListView.as_view(), name='team_attendance_list'),
    path('org/', OrgAttendanceListView.as_view(), name='org_attendance_list'),
    path('org/export/', ExportAttendanceCSVView.as_view(), name='export_attendance_csv'),
]
