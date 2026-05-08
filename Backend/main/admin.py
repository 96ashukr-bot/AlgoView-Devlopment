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
    search_fields = ['user__email',]
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
    list_display=('id','name','execution_mode','multi_leg_template')
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
    list_display=("id",'client','broker','symbol', 'updated_at', 'group_service','segment','is_tread_status') 
    search_fields = ('client__email', 'symbol','group_service') 
    readonly_fields = ("updated_at",)

@admin.register(TradeLog)    
class TradeLogAdmin(admin.ModelAdmin):
    list_display=("id",'client','is_trade_status') 

@admin.register(TradingLog)    
class TradeLogAdmin(admin.ModelAdmin):
    list_display=("id",'date','client','symbol')     

@admin.register(ClientBrokerdetails)    
class ClientBrokerDetailgAdmin(admin.ModelAdmin):
    list_display=("id",'client','broker_name','execution_node','tokenCreatedAt','access_token_expiry')   
    search_fields = ("id", "client__email", "broker_name__broker_name")    


@admin.action(description="Mark selected nodes broker verified")
def mark_nodes_verified(modeladmin, request, queryset):
    queryset.update(is_verified_with_broker=True)


@admin.action(description="Disable selected nodes")
def disable_nodes(modeladmin, request, queryset):
    queryset.update(is_active=False, status=ExecutionNode.STATUS_DISABLED)


@admin.action(description="Release selected nodes from clients")
def release_nodes_from_client(modeladmin, request, queryset):
    for node in queryset.select_related("assigned_client"):
        client = node.assigned_client
        node.assigned_client = None
        node.status = ExecutionNode.STATUS_FREE if node.is_active else ExecutionNode.STATUS_DISABLED
        node.save(update_fields=["assigned_client", "status", "updated_at"])
        ClientBrokerdetails.objects.filter(execution_node=node).update(execution_node=None)
        node.mark_log("released", "Node released from client via admin.", client=client)


@admin.register(ExecutionNode)
class ExecutionNodeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "ip_address",
        "provider",
        "assigned_client",
        "status",
        "last_heartbeat",
        "is_verified_with_broker",
        "is_active",
    )
    list_filter = ("status", "is_active", "is_verified_with_broker", "provider")
    search_fields = ("name", "ip_address", "node_id", "assigned_client__email", "assigned_client__fullName")
    readonly_fields = ("last_heartbeat", "last_seen_ip", "created_at", "updated_at")
    actions = (mark_nodes_verified, disable_nodes, release_nodes_from_client)


@admin.register(ExecutionOrderJob)
class ExecutionOrderJobAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "execution_node", "broker_details", "symbol", "transaction_type", "quantity", "status", "retry_count", "created_at")
    list_filter = ("status", "execution_node", "broker_details__broker_name")
    search_fields = ("idempotency_key", "client__email", "symbol", "token")
    readonly_fields = ("idempotency_key", "created_at", "updated_at")


@admin.register(ExecutionNodeLog)
class ExecutionNodeLogAdmin(admin.ModelAdmin):
    list_display = ("id", "execution_node", "client", "event_type", "message", "created_at")
    list_filter = ("event_type", "execution_node")
    search_fields = ("execution_node__node_id", "client__email", "message")
    readonly_fields = ("created_at",)

@admin.register(Tradeorderhistory)    
class ClientTradeHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "history_id", "transaction_type", "trading_symbol", "date", "strategy", "GroupService", "order_id", "broker", "order_status", "SignalEntry_time")     
    search_fields = ("id", "client__email")  # Change to a valid related field

  
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
    
@admin.register(GroupService)
class GroupServiceAdmin(admin.ModelAdmin):
    list_display = ['id','group_name','segment']         


@admin.register(ClientMultiLegStrategySetting)
class ClientMultiLegStrategySettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'strategy', 'group_service', 'broker', 'quantity', 'is_tread_status', 'updated_at')
    search_fields = ('client__email', 'client__fullName', 'strategy__name', 'group_service')


@admin.register(StrategyExecution)
class StrategyExecutionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'client',
        'strategy_name',
        'underlying',
        'broker',
        'status',
        'total_quantity',
        'combined_pnl',
        'entry_time',
        'exit_time',
        'updated_at',
    )
    list_filter = ('status', 'broker', 'strategy_name')
    search_fields = ('client__email', 'client__fullName', 'strategy_name', 'underlying', 'idempotency_key')


@admin.register(StrategyLeg)
class StrategyLegAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'strategy_execution',
        'leg_name',
        'transaction_type',
        'option_type',
        'strike_price',
        'quantity',
        'status',
        'broker_order_id',
        'updated_at',
    )
    list_filter = ('status', 'transaction_type', 'option_type', 'exchange')
    search_fields = ('symbol', 'token', 'broker_order_id', 'strategy_execution__client__email')


@admin.register(StrategyExecutionLog)
class StrategyExecutionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'strategy_execution', 'event_type', 'created_at')
    list_filter = ('event_type',)
    search_fields = ('strategy_execution__client__email', 'message')
