from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """
    Allows access only to administrator users or superusers.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and (
                request.user.role == 'admin' or request.user.is_superuser
            )
        )

class IsManagerOfEmployee(BasePermission):
    """
    Allows access to managers or admins who supervise the given employee/object.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and (
                request.user.role in ['manager', 'admin'] or request.user.is_superuser
            )
        )

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or user.role == 'admin':
            return True

        employee = getattr(obj, 'employee', obj)
        return bool(
            employee.manager == user or (
                user.department and employee.department == user.department
            )
        )

class IsOwnerOrManager(BasePermission):
    """
    Allows object-level access to the object's owner (employee), their manager, or an admin.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or user.role == 'admin':
            return True

        employee = getattr(obj, 'employee', obj)
        if employee == user:
            return True

        return bool(
            user.role == 'manager' and (
                employee.manager == user or (
                    user.department and employee.department == user.department
                )
            )
        )
