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
        ('Personal info', {'fields': ('firstName', 'lastName','phoneNumber','middleName', 'profilePicture', 'role', 'assigned_client','created_by', 'PANEL_CLIENT_KEY', 'start_date', 'end_date', 'client_type', 'is_password_temporary', 'is_new_password',
            # Permanent Address Fields
            'permanent_add_line_1', 'permanent_add_line_2', 'permanent_city', 
            'permanent_state', 'permanent_country', 'permanent_zip_code','is_address_same',
            # Current Address Fields
            'current_add_line_1', 'current_add_line_2', 'current_city',
            'current_state', 'current_country', 'current_zip_code','external_user','type_of_user','Group_service',
            'Strategy','Broker','license','to_month','is_client','client_status','start_date_client','end_date_client' ,'is_enable','client_expiry_status')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser','created_at')}),
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
    list_display = ['id','user','otp_code','is_verified']
    search_fields = ['user',]
    ordering = ['user',]

admin.site.register(Permission)
admin.site.register(RolePermission)

@admin.register(SignalOrderLog)
class SignalOrderLogAdmin(admin.ModelAdmin):
    list_display = ['id','order_type','json_data','symbol','created_at']
    # search_fields = ['order_type',]
    # ordering = ['order_type',]       
    
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
@admin.register(SubSegment)
class SubSegmentAdmin(admin.ModelAdmin):
    list_display=('id','name','token','Exchange')    
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

@admin.register(ClientTradeSetting)    
class ClientTradeSettingAdmin(admin.ModelAdmin):
    list_display=("id",'client','broker','symbol','segment','is_tread_status') 

@admin.register(TradeLog)    
class TradeLogAdmin(admin.ModelAdmin):
    list_display=("id",'client','is_trade_status') 

@admin.register(TradingLog)    
class TradeLogAdmin(admin.ModelAdmin):
    list_display=("id",'date','client')     

@admin.register(ClientBrokerdetails)    
class ClientBrokerDetailgAdmin(admin.ModelAdmin):
    list_display=("id",'client','broker_name')   
    
@admin.register(Tradeorderhistory)    
class ClientTradeHistoryAdmin(admin.ModelAdmin):
    list_display=("id",'client','transaction_type','trading_symbol','date','order_id','broker','order_status',"SignalEntry_time")     
  
  
@admin.register(CompanyProfileDetails)   
class CompanyProfileDetailsAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'company_email', 'company_phone_number', 'company_logo')
    search_fields = ('company_name', 'company_email')
    list_filter = ('company_name',)
    
@admin.register(CompanySmtpDetails)   
class CompanySmtpDetailsAdmin(admin.ModelAdmin):
    list_display = ('email_host', 'email_port', 'email_use_tls', 'email_host_user')
    search_fields = ('email_host', 'email_host_user')    
    
@admin.register(AdminLicense)   
class LiecensdetailsAdmin(admin.ModelAdmin):
    list_display =('id','sub_admin')
@admin.register(Payment)   
class PaymentdetailsAdmin(admin.ModelAdmin):
    list_display = ('id','sub_admin')    
    
@admin.register(WebsocketDetails)
class WebsocketDetailsAdmin(admin.ModelAdmin):  
    list_display = ('id','token_status')     