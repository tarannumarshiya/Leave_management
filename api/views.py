from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from users.models import User, Department
from attendance.models import Attendance
from leave.models import LeaveType, LeaveBalance, LeaveRequest

from .serializers import (
    UserSerializer,
    DepartmentSerializer,
    AttendanceSerializer,
    LeaveTypeSerializer,
    LeaveBalanceSerializer,
    LeaveRequestSerializer
)
from .permissions import IsAdmin, IsOwnerOrManager, IsManagerOfEmployee

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().order_by('name')
    serializer_class = DepartmentSerializer
    filterset_fields = ['is_active', 'code']
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code', 'id']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    filterset_fields = ['role', 'department', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'employee_id']
    ordering_fields = ['username', 'date_joined_org', 'id']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return User.objects.all().select_related('department', 'manager').order_by('username')
        elif user.role == 'manager':
            query = Q(manager=user)
            if user.department:
                query = query | Q(department=user.department)
            return User.objects.filter(query).select_related('department', 'manager').order_by('username')
        else:
            return User.objects.filter(pk=user.pk).select_related('department', 'manager')

class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [IsOwnerOrManager]
    filterset_fields = ['date', 'status', 'employee', 'employee__department']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name']
    ordering_fields = ['date', 'check_in_time', 'id']

    def get_queryset(self):
        user = self.request.user
        queryset = Attendance.objects.all().select_related('employee', 'employee__department')
        if user.is_superuser or user.role == 'admin':
            return queryset.order_by('-date')
        elif user.role == 'manager':
            query = Q(employee=user) | Q(employee__manager=user)
            if user.department:
                query = query | Q(employee__department=user.department)
            return queryset.filter(query).order_by('-date')
        else:
            return queryset.filter(employee=user).order_by('-date')

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)

class LeaveTypeViewSet(viewsets.ModelViewSet):
    queryset = LeaveType.objects.all().order_by('name')
    serializer_class = LeaveTypeSerializer
    filterset_fields = ['name']
    search_fields = ['name']
    ordering_fields = ['name', 'max_days_per_year']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

class LeaveBalanceViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveBalanceSerializer
    permission_classes = [IsOwnerOrManager]
    filterset_fields = ['year', 'leave_type', 'employee', 'employee__department']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name']
    ordering_fields = ['year', 'employee__username', 'id']

    def get_queryset(self):
        user = self.request.user
        queryset = LeaveBalance.objects.all().select_related('employee', 'employee__department', 'leave_type')
        if user.is_superuser or user.role == 'admin':
            return queryset.order_by('-year', 'employee__username')
        elif user.role == 'manager':
            query = Q(employee=user) | Q(employee__manager=user)
            if user.department:
                query = query | Q(employee__department=user.department)
            return queryset.filter(query).order_by('-year', 'employee__username')
        else:
            return queryset.filter(employee=user).order_by('-year')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsOwnerOrManager()]

class LeaveRequestViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsOwnerOrManager]
    filterset_fields = ['status', 'leave_type', 'start_date', 'end_date', 'employee', 'employee__department']
    search_fields = ['employee__username', 'employee__first_name', 'reason']
    ordering_fields = ['applied_on', 'start_date', 'id']

    def get_queryset(self):
        user = self.request.user
        queryset = LeaveRequest.objects.all().select_related('employee', 'employee__department', 'leave_type', 'approved_by')
        if user.is_superuser or user.role == 'admin':
            return queryset.order_by('-applied_on')
        elif user.role == 'manager':
            query = Q(employee=user) | Q(employee__manager=user)
            if user.department:
                query = query | Q(employee__department=user.department)
            return queryset.filter(query).order_by('-applied_on')
        else:
            return queryset.filter(employee=user).order_by('-applied_on')

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user, status='pending')

    @action(detail=True, methods=['post'], permission_classes=[IsManagerOfEmployee])
    def approve(self, request, pk=None):
        leave_request = self.get_object()
        leave_request.status = 'approved'
        leave_request.approved_by = request.user
        leave_request.decision_note = request.data.get('decision_note', '')
        leave_request.save()
        return Response(LeaveRequestSerializer(leave_request, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsManagerOfEmployee])
    def reject(self, request, pk=None):
        leave_request = self.get_object()
        leave_request.status = 'rejected'
        leave_request.approved_by = request.user
        leave_request.decision_note = request.data.get('decision_note', '')
        leave_request.save()
        return Response(LeaveRequestSerializer(leave_request, context={'request': request}).data)
