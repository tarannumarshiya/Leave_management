from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

from .views import (
    DepartmentViewSet,
    UserViewSet,
    AttendanceViewSet,
    LeaveTypeViewSet,
    LeaveBalanceViewSet,
    LeaveRequestViewSet
)

router = DefaultRouter()
router.register('departments', DepartmentViewSet, basename='department')
router.register('users', UserViewSet, basename='user')
router.register('attendance', AttendanceViewSet, basename='attendance')
router.register('leave-types', LeaveTypeViewSet, basename='leavetype')
router.register('leave-balances', LeaveBalanceViewSet, basename='leavebalance')
router.register('leave-requests', LeaveRequestViewSet, basename='leaverequest')

urlpatterns = [
    # Router endpoints
    path('', include(router.urls)),
    
    # JWT Authentication Endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # OpenAPI Schema & Swagger API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
