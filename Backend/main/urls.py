from django.conf import settings
from django.urls import path
from .views import *
from django.conf.urls.static import static
urlpatterns = [
    path('signup/', UserRegistrationView.as_view(), name='user-registration'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('verify-otp/', OTPVerifyView.as_view(), name='otp_verify'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('create-roles/', RoleListCreateView.as_view(), name='role-list-create'),
    path('roles/<int:pk>/', RoleDetailView.as_view(), name='role-detail'),
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('user-assign-role/', UserAssignRoleView.as_view(), name='user-assign-role'),
    path('user-management/', UserManagementView.as_view(), name='user-management'),
    path('user-management/<int:pk>/', UserManagementView.as_view(), name='user-detail-management'),
    path('kyc/', KYCListCreateView.as_view(), name='kyc-list-create'),
    path('kyc/<int:pk>/', KYCDetailView.as_view(), name='kyc-detail'),

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

