from django.conf import settings
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from main.permissions import RolePermissionListView, UpdateRolePermissionsView
from .views import *
from django.conf.urls.static import static
urlpatterns = [
    path('signup/', UserRegistrationView.as_view(), name='user-registration'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('verify-otp/', OTPVerifyView.as_view(), name='otp_verify'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('create-roles/', RoleListCreateView.as_view(), name='role-list-create'),
    path('get-roles-list/', RoleListCreateView.as_view(), name='role-list'),
    path('delete-roles/<int:id>/', RoleDeleteView.as_view(), name='role-delete'),
    path('roles/<int:pk>/', RoleDetailView.as_view(), name='role-detail'),
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('user-assign-role/', UserAssignRoleView.as_view(), name='user-assign-role'),
    path('user-management/', UserManagementView.as_view(), name='user-management'),
    path('user-management/<int:pk>/', UserManagementView.as_view(), name='user-detail-management'),
    path('user-profile/', UserProfileView.as_view(), name='user-profile'),
    path('kyc/', KYCListCreateView.as_view(), name='kyc-list-create'),
    path('kyc/<int:pk>/', KYCDetailView.as_view(), name='kyc-detail'),
    path('pending-kyc-list/', PendingKYCListView.as_view(), name='kyc-pending-list'),
    path('kyc/verify/<int:kyc_id>/', KYCVerificationView.as_view(), name='kyc-verification'),
    path('update-role-permissions/<int:role_id>/', UpdateRolePermissionsView.as_view(), name='update-role-permissions'),
    path('role-permissions/', RolePermissionListView.as_view(), name='role-permissions-list'),
    path('v1/algo/webhook/', TradingViewWebhook.as_view(), name='webhook'),
    path('get-alice-orders/', GetAliceOrderBook.as_view(), name='get-order-book'),
    path('get-alice-tread-history/', GetAliceTreadBook.as_view(), name='get-tread-book'),
    path('order-logs-list/', OrderLogListView.as_view(), name='order-log-list'),
    
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

