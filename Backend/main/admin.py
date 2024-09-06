from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import  OTP, User, Role, KYC

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'fullName', 'phoneNumber', 'role', 'is_active', 'is_staff', 'is_superuser']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'firstName', 'lastName', 'phoneNumber']
    ordering = ['email']

    # Optionally, you can add additional configurations for form fields and fieldsets if needed
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('firstName', 'lastName', 'phoneNumber', 'profilePicture', 'role','is_password_temporary','is_new_password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'firstName', 'lastName', 'phoneNumber', 'profilePicture', 'role', 'password1', 'password2'),
        }),
    )
    filter_horizontal = ()

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name','status']
    search_fields = ['name']
    ordering = ['name']

@admin.register(KYC)
class KycAdmin(admin.ModelAdmin):
    list_display = ['user','document_type','document_file']
    search_fields = ['user','document_type']
    ordering = ['user','document_type']
    
@admin.register(OTP)
class OtpAdmin(admin.ModelAdmin):
    list_display = ['user','otp_code','is_verified']
    search_fields = ['user',]
    ordering = ['user',]