from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import *
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'fullName', 'phoneNumber', 'role', 'is_active', 'is_staff', 'is_superuser', 'created_at', 'updated_at']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'firstName', 'lastName', 'phoneNumber']
    ordering = ['email']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('firstName', 'lastName','phoneNumber', 'profilePicture', 'role',  'PANEL_CLIENT_KEY', 'start_date', 'end_date', 'client_type', 'is_password_temporary', 'is_new_password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        # ('Metadata', {'fields': ('created_at', 'updated_at')}),  # Add 'created_at' and 'updated_at' here
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
    list_display = ['document_type','is_verified','status','verified_by']
    search_fields = ['document_type','is_verified','status']
    ordering = ['document_type','is_verified','status']
    
@admin.register(OTP)
class OtpAdmin(admin.ModelAdmin):
    list_display = ['user','otp_code','is_verified']
    search_fields = ['user',]
    ordering = ['user',]

admin.site.register(Permission)
admin.site.register(RolePermission)

@admin.register(OrderLog)
class OtpAdmin(admin.ModelAdmin):
    list_display = ['symbol','order_type','strategy','price','created_at']
    search_fields = ['order_type',]
    ordering = ['order_type',]       