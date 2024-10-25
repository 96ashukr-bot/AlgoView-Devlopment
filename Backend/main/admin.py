from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import *
@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ['id','email', 'fullName', 'phoneNumber', 'role', 'is_active', 'is_staff', 'is_superuser', 'created_at', 'updated_at']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'firstName', 'lastName', 'phoneNumber']
    ordering = ['email']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('firstName', 'lastName','phoneNumber','middleName', 'profilePicture', 'role', 'assigned_client','created_by', 'PANEL_CLIENT_KEY', 'start_date', 'end_date', 'client_type', 'is_password_temporary', 'is_new_password'
            , 
            # Permanent Address Fields
            'permanent_add_line_1', 'permanent_add_line_2', 'permanent_city', 
            'permanent_state', 'permanent_country', 'permanent_zip_code',
            # Current Address Fields
            'current_add_line_1', 'current_add_line_2', 'current_city',
            'current_state', 'current_country', 'current_zip_code','external_user','type_of_user','Group_service',
            'Strategy','Broker','license','to_month','client_status','start_date_client','end_date_client')}),
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
    list_display = ['user','id_proof','is_verified','address_proof_id','status','verified_by']
    search_fields = ['id_proof','is_verified','status']
    ordering = ['id_proof','is_verified','status']
    
@admin.register(OTP)
class OtpAdmin(admin.ModelAdmin):
    list_display = ['user','otp_code','is_verified']
    search_fields = ['user',]
    ordering = ['user',]

admin.site.register(Permission)
admin.site.register(RolePermission)

@admin.register(OrderLog)
class OtpAdmin(admin.ModelAdmin):
    list_display = ['symbol','order_type','strategy','price','created_at','json_data']
    search_fields = ['order_type',]
    ordering = ['order_type',]       
    
@admin.register(UserActivityLog)
class UserActivity_logs(admin.ModelAdmin):
    list_display = ['user','action_type','last_login_time']
@admin.register(GroupService)
class GroupServicelogs(admin.ModelAdmin):
    list_display = ['id','group_name','segment']       
    
@admin.register(State)
class StatesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'country_id', 'country_code', 'state_code')  # Fields to display in the list view
    search_fields = ('name', 'country_code')  # Fields to search in the admin interface
    ordering = ('name',)  # Default ordering
@admin.register(cities)
class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'state_id', 'state_code',)  # Fields to display in the list view
    search_fields = ('name',)  # Fields to search in the admin interface
    list_filter = ('state_id',)  # Allows filtering by state    
    
@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    list_display=('id','name')  

@admin.register(License)
class LiecensAdmin(admin.ModelAdmin):
    list_display=('id','name',"no_of_days_month",'created_at','updated_at')          

@admin.register(Strategies)
class StrategyAdmin(admin.ModelAdmin):
    list_display=('id','name',)      
@admin.register(Broker)
class BrokersAdmin(admin.ModelAdmin):
    list_display=('id','broker_name','is_active','description')    
@admin.register(Services)
class ServicesAdmin(admin.ModelAdmin):
    list_display=('id','service_name')   
@admin.register(categories)
class categoriesAdmin(admin.ModelAdmin):
    list_display=('id','name')       
      