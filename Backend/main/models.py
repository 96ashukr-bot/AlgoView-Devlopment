import datetime
import random
from django.utils.timezone import now
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
# from django.utils import timezone
# from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from datetime import datetime,timedelta  # Import timedelta from datetime
from django.utils import timezone  # To handle timezones correctly in Djang
from pytz import timezone as pytz_timezone

from main.angelone.utils.crypto import decrypt_value, encrypt_value
from main.broker_registry import normalize_broker_name
def get_ist_time():
    # Convert the current UTC time to IST
    ist_timezone = pytz_timezone('Asia/Kolkata')
    return now().astimezone(ist_timezone)
class Role(models.Model):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    
    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=ACTIVE)
    created_at = models.DateTimeField(default=get_ist_time)
    updated_at = models.DateTimeField(default=get_ist_time)
    def __str__(self):
        return self.name

class UserManager(BaseUserManager):
    def create_user(self, email, firstName, lastName, phoneNumber, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)

        user = self.model(email=email, firstName=firstName, lastName=lastName, phoneNumber=phoneNumber, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, firstName, lastName, phoneNumber, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        
        # Superuser creation does not need to validate the role, but this check is optional
        return self.create_user(email, firstName, lastName, phoneNumber, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True,null=True, blank=True)
    phoneNumber = models.CharField(max_length=15, null=True, blank=True)
    firstName = models.CharField(max_length=150,null=True, blank=True)
    middleName = models.CharField(max_length=150,null=True,blank=True)
    lastName = models.CharField(max_length=150,blank=True,null=True)
    userName = models.CharField(max_length=150,blank=True,null=True)
    fullName = models.CharField(max_length=300, blank=True, editable=False,null=True)  # Will be automatically generated
    profilePicture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL,null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_password_temporary = models.BooleanField(default=True)  # New field to check if password is temporary
    is_new_password = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)      
    # New fields for user profile
    PANEL_CLIENT_KEY = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    client_type = models.CharField(max_length=50, blank=True, null=True) 
    is_enable = models.BooleanField(default=False)

    # Permanent Address Fields
    permanent_add_line_1 = models.CharField(max_length=255, null=True, blank=True)
    permanent_add_line_2 = models.CharField(max_length=255, null=True, blank=True)
    permanent_city = models.CharField(max_length=100, null=True, blank=True)
    permanent_state = models.CharField(max_length=50, null=True, blank=True)
    permanent_country = models.CharField(max_length=20, null=True, blank=True)
    permanent_zip_code = models.CharField(max_length=20, null=True, blank=True)
    
    is_address_same = models.BooleanField(default=False)
    # Current Address Fields
    current_add_line_1 = models.CharField(max_length=255, null=True, blank=True)
    current_add_line_2 = models.CharField(max_length=255, null=True, blank=True)
    current_city = models.CharField(max_length=100, null=True, blank=True)
    current_state = models.CharField(max_length=50, null=True, blank=True)
    current_country = models.CharField(max_length=20, null=True, blank=True)
    current_zip_code = models.CharField(max_length=20, null=True, blank=True)

    external_user = models.CharField(max_length=50, null=True, blank=True)
    Group_service = models.ForeignKey('GroupService', on_delete=models.SET_NULL, null=True, blank=True, related_name='group_Service')
    Broker=models.ForeignKey('Broker', on_delete=models.SET_NULL,null=True, blank=True,  related_name='group_Broker')
    license=models.ForeignKey('License', on_delete=models.SET_NULL, null=True, blank=True, related_name='client_license')
    to_month=models.IntegerField(null=True, blank=True)
    # Hierarchy tracking
    created_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='created_users')    

    # Clients associated with this user (single assignment)
    assigned_client = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL,related_name='assigned_users')
    client_status   = models.BooleanField(default=True)
    is_client       = models.CharField(max_length=50, null=True, blank=True)
    client_key      = models.CharField(max_length=50, null=True, blank=True)
    demate_acc_uid  = models.CharField(max_length=150,blank=True,null=True)
    client_secrete  = models.CharField(max_length=50, null=True, blank=True)
    user_license_month= models.IntegerField(blank=True,null=True)
    Strategy = models.ManyToManyField("Strategies", related_name='client_strategy', blank=True)
    start_date_client = models.DateField(null=True, blank=True)
    end_date_client   = models.DateField(null=True, blank=True)
    givenservices_to_month  = models.CharField(max_length=50, null=True, blank=True)
    # assigned_clients = models.ManyToManyField('self', symmetrical=False, related_name='assigned_users', blank=True)
    type_of_user=models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=get_ist_time)
    client_expiry_status=models.BooleanField(default=False)
    #client penle Run Algo form
    objects     = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['firstName','lastName', 'phoneNumber']

    def __str__(self):
        return self.email
    # def save(self, *args, **kwargs):
    #     # Automatically populate fullName if it is not already set
    #     if not self.fullName:
    #         self.fullName = f"{self.firstName} {self.middleName or ''} {self.lastName}".strip()
    #     super().save(*args, **kwargs)
    def get_full_name(self):
        return f"{self.firstName} {self.lastName}"

    def get_short_name(self):
        return self.firstName

    def save(self, *args, **kwargs):
        if not self.fullName:
            self.fullName = f"{self.firstName} {self.middleName or ''} {self.lastName}".strip()
        if self.middleName:
            self.fullName = f"{self.firstName}  {self.middleName} {self.lastName}"
        else:
            
            self.fullName = f"{self.firstName} {self.lastName} "
        self.calculate_dates()    
        super().save(*args, **kwargs)
    
    def calculate_dates(self):
        """Calculate client service dates from the selected license."""
        today = timezone.localdate()
        license_type = (getattr(self.license, 'name', '') or '').strip().lower()

        if license_type == "live":
            try:
                months = int(self.to_month or 0)
            except (TypeError, ValueError):
                months = 0

            if 1 <= months <= 12:
                self.to_month = months
                self.start_date_client = today
                self.end_date_client = today + relativedelta(months=months)
            else:
                self.start_date_client = None
                self.end_date_client = None
        elif license_type == "demo":
            self.to_month = None
            self.start_date_client = today
            self.end_date_client = today + timedelta(days=5)
        else:
            self.to_month = None
            self.start_date_client = None
            self.end_date_client = None
                
            
class KYC(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL,blank=True, null=True,related_name='kyc_user')
    id_proof = models.CharField(max_length=50)
    document_file_front = models.FileField(upload_to='kyc_documents/front/', blank=True)
    document_file_back = models.FileField(upload_to='kyc_documents/back/', blank=True)
    is_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # Add status field
    verified_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='verified_kyc')  # Admin who verified
    created_at = models.DateTimeField(default=get_ist_time)
    updated_at = models.DateTimeField(default=get_ist_time)
    # New fields
    address_proof_id = models.CharField(max_length=100, blank=True)  # To store address ID or code
    address_prof_front = models.FileField(upload_to='kyc_documents/address_front/', blank=True)  # Address proof front
    address_prof_back = models.FileField(upload_to='kyc_documents/address_back/', blank=True)  # Address proof back
  
    
class OTP(models.Model):
    user = models.ForeignKey(User,null=True, on_delete=models.SET_NULL,related_name='user_otp' )
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=get_ist_time)
    is_verified = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)

    def generate_otp(self):
        self.otp_code = random.randint(100000, 999999)
        self.expires_at = get_ist_time() + timedelta(seconds=120)  # Set expiration to 120 seconds from now
        # Set expiration to 120 seconds from now
        self.is_verified = False
        self.save()
        
    def is_expired(self):
        return get_ist_time() > self.expires_at if self.expires_at else True
    def __str__(self):
        return f"{self.user.email} OTP"


# Custom Permission Model
class Permission(models.Model):
    group = models.CharField(max_length=100, default=None, null=True, blank=True)  # Permission Group (optional)
    permission = models.CharField(max_length=100, default=None, null=True, blank=True)  # Permission Name
    description = models.TextField(null=True, blank=True)  # Optional Description of Permission
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.group} - {self.permission}" if self.group else self.permission
    
# RolePermission Model: Links Role to Permissions
class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL,null=True, blank=True,related_name='user_role' )
    permissions = models.ManyToManyField(Permission, related_name="role_permissions", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.role.name} - Permissions" 
    
#order-logs
class SignalOrderLog(models.Model):
    signal_time = models.DateTimeField()  # Time of the signal
    order_type = models.CharField(max_length=250,null=True, blank=True)  # 'LX' or 'LE' (Type)
    symbol = models.CharField(max_length=100,null=True, blank=True)  # Symbol (e.g., BANKNIFTY)
    price = models.DecimalField(max_digits=50, decimal_places=2,null=True, blank=True)  # Price
    strategy = models.CharField(max_length=100,null=True, blank=True)  # Strategy (e.g., Support & Resistance)
    created_at = models.DateTimeField(auto_now_add=True)
    # user = models.ForeignKey(User, on_delete=models.SET_NULL,null=True, blank=True,related_name='user_log')
    # status = models.CharField(max_length=20, default="Pending")  # "Success", "Failed"
    # failure_reason = models.TextField(null=True, blank=True)  # Reason for failure (optional)
    json_data = models.JSONField(null=True, blank=True)
    def __str__(self):
        return f"{self.signal_time} - {self.order_type} - {self.symbol} - {self.price}"   
    
#user last login ip activtity log
class UserActivityLog(models.Model):
    ACTION_TYPES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL,null=True, blank=True, related_name='user_activty_log')
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES)
    last_login_time = models.DateTimeField(null=True, blank=True)
    last_logout_time = models.DateTimeField(null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)  # Store session key for reference
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.email} - {self.last_login_time}'

    def mark_logout(self):
        """ Marks logout time when the user logs out """
        self.last_logout_time = now()
        self.save()        

class State(models.Model):
    id = models.AutoField(primary_key=True) 
    name = models.CharField(max_length=255) 
    country_id = models.IntegerField()
    country_code = models.TextField(null=True, blank=True)
    state_code = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name 
class cities(models.Model):
    name = models.CharField(max_length=150)
    state_id = models.ForeignKey( State, on_delete=models.SET_NULL,null=True, blank=True,related_name='cities' )
    state_code = models.TextField(null=True, blank=True)


    def __str__(self):
        return self.name
    
class License(models.Model):
    name=models.CharField(max_length=255,null=True)    
    no_of_days_month=models.IntegerField(blank=True,null=True)
    period=models.CharField(max_length=255,null=True,blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True)
    def __str__(self):
        return self.name
class categories(models.Model):
    name=models.CharField(max_length=255,null=True)    
    status = models.BooleanField(default=True)
    def __str__(self):
        return self.name    
class Segment(models.Model):
    name = models.CharField(max_length=150)
    short_name = models.CharField(null=True, blank=True,max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True)
    def __str__(self):
        return self.name  
class SubSegment(models.Model):
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name='sub_segments')
    name = models.CharField(max_length=150)
    short_name = models.CharField(max_length=150, null=True, blank=True)
    status = models.BooleanField(default=True)
    token=models.IntegerField(blank=True,null=True)
    Exchange=models.CharField(max_length=150,blank=True,null=True)
    def __str__(self):
        return f" {self.name}"


    
class Services(models.Model):
    service_name = models.CharField(max_length=100)
    segment = models.ForeignKey(Segment, on_delete=models.SET_NULL, null=True, blank=True,related_name='service_segments')
    category= models.ForeignKey(categories, on_delete=models.SET_NULL,null=True, blank=True, related_name='services_categories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.service_name
class Strategies(models.Model):
    EXECUTION_MODE_INDICATOR = "INDICATOR_BASED"
    EXECUTION_MODE_MULTI_LEG = "MULTI_LEG"
    EXECUTION_MODE_CHOICES = (
        (EXECUTION_MODE_INDICATOR, "Indicator Based Strategies"),
        (EXECUTION_MODE_MULTI_LEG, "Multi Leg Option Strategies"),
    )

    MULTI_LEG_SHORT_STRADDLE = "SHORT_STRADDLE"
    MULTI_LEG_BULL_CALL_SPREAD = "BULL_CALL_SPREAD"
    MULTI_LEG_BEAR_CALL_SPREAD = "BEAR_CALL_SPREAD"
    MULTI_LEG_BEAR_PUT_SPREAD = "BEAR_PUT_SPREAD"
    MULTI_LEG_LONG_CALL_BUTTERFLY = "LONG_CALL_BUTTERFLY"
    MULTI_LEG_SHORT_CALL_BUTTERFLY = "SHORT_CALL_BUTTERFLY"
    MULTI_LEG_LONG_CALL_CONDOR = "LONG_CALL_CONDOR"
    MULTI_LEG_SHORT_CALL_CONDOR = "SHORT_CALL_CONDOR"
    MULTI_LEG_LONG_IRON_CONDOR = "LONG_IRON_CONDOR"
    MULTI_LEG_SHORT_IRON_BUTTERFLY = "SHORT_IRON_BUTTERFLY"
    MULTI_LEG_TEMPLATE_CHOICES = (
        (MULTI_LEG_SHORT_STRADDLE, "Short Straddle"),
        (MULTI_LEG_BULL_CALL_SPREAD, "Bull Call Spread"),
        (MULTI_LEG_BEAR_CALL_SPREAD, "Bear Call Spread"),
        (MULTI_LEG_BEAR_PUT_SPREAD, "Bear Put Spread"),
        (MULTI_LEG_LONG_CALL_BUTTERFLY, "Long Call Butterfly"),
        (MULTI_LEG_SHORT_CALL_BUTTERFLY, "Short Call Butterfly"),
        (MULTI_LEG_LONG_CALL_CONDOR, "Long Call Condor"),
        (MULTI_LEG_SHORT_CALL_CONDOR, "Short Call Condor"),
        (MULTI_LEG_LONG_IRON_CONDOR, "Long Iron Condor"),
        (MULTI_LEG_SHORT_IRON_BUTTERFLY, "Short Iron Butterfly"),
    )

    name = models.CharField(max_length=150)
    Lots=models.IntegerField(blank=True,null=True)
    segment = models.ForeignKey(Segment, on_delete=models.SET_NULL, null=True, blank=True, related_name='strategy_segments')
    category = models.ForeignKey(categories, on_delete=models.SET_NULL, null=True, blank=True, related_name='strategy_categories')
    execution_mode = models.CharField(
        max_length=30,
        choices=EXECUTION_MODE_CHOICES,
        default=EXECUTION_MODE_INDICATOR,
    )
    multi_leg_template = models.CharField(
        max_length=40,
        choices=MULTI_LEG_TEMPLATE_CHOICES,
        null=True,
        blank=True,
    )
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_submit= models.BooleanField(default=True)
    Indicator=models.ImageField(upload_to='strategy/Indicator', null=True, blank=True)
    Strategy_Tester=models.ImageField(upload_to='strategy/Strategy_Tester', null=True, blank=True)
    Strategy_Logo=models.ImageField(upload_to='strategy/Strategy_Logo', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True)

    # Pricing Options,
    monthly_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quarterly_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    half_yearly_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    yearly_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
        # Add Many-to-Many relationship with User (clients)
    clients = models.ManyToManyField(User, related_name='strategies', blank=True)

    def __str__(self):
        return self.name


class ClientMultiLegStrategySetting(models.Model):
    ORDER_TYPE_CHOICES = (
        ("MARKET", "MARKET"),
        ("LIMIT", "LIMIT"),
    )

    client = models.ForeignKey('User', on_delete=models.CASCADE, related_name='multi_leg_trade_settings')
    strategy = models.ForeignKey('Strategies', on_delete=models.CASCADE, related_name='client_multi_leg_settings')
    segment = models.ForeignKey('Segment', on_delete=models.SET_NULL, null=True, blank=True)
    underlying = models.CharField(max_length=30, default="NIFTY", null=True, blank=True)
    group_service = models.CharField(max_length=255, null=True, blank=True)
    broker = models.CharField(max_length=50, null=True, blank=True)
    product_type = models.CharField(max_length=20, null=True, blank=True)
    order_type = models.CharField(
        max_length=20,
        choices=ORDER_TYPE_CHOICES,
        default="LIMIT",
        null=True,
        blank=True,
    )
    buffer_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    trade_limit = models.IntegerField(null=True, blank=True)
    max_loss_for_day = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_profit_for_day = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_tread_status = models.BooleanField(default=False)
    sl_type = models.CharField(max_length=50, null=True, blank=True)
    stop_loss = models.IntegerField(null=True, blank=True)
    target = models.IntegerField(null=True, blank=True)
    legs = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('client', 'strategy')

    def __str__(self):
        return f"{self.client_id}-{self.strategy_id}-{self.strategy.name}"


class StrategyExecution(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_EXECUTING = "EXECUTING"
    STATUS_ACTIVE = "ACTIVE"
    STATUS_EXITING = "EXITING"
    STATUS_EXITED = "EXITED"
    STATUS_FAILED = "FAILED"
    STATUS_ROLLED_BACK = "ROLLED_BACK"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_EXECUTING, "Executing"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_EXITING, "Exiting"),
        (STATUS_EXITED, "Exited"),
        (STATUS_FAILED, "Failed"),
        (STATUS_ROLLED_BACK, "Rolled Back"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    client = models.ForeignKey('User', on_delete=models.CASCADE, related_name='strategy_executions')
    broker = models.CharField(max_length=100)
    strategy_name = models.CharField(max_length=100)
    underlying = models.CharField(max_length=100)
    expiry = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    entry_time = models.DateTimeField(null=True, blank=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    total_quantity = models.IntegerField(default=0)
    combined_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    max_pnl_seen = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    trailing_stop_level = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    exit_reason = models.CharField(max_length=255, null=True, blank=True)
    idempotency_key = models.CharField(max_length=150, unique=True, null=True, blank=True)
    config_snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.strategy_name}#{self.id} - {self.client_id}"


class StrategyLeg(models.Model):
    STATUS_PLANNED = "PLANNED"
    STATUS_EXECUTING = "EXECUTING"
    STATUS_ACTIVE = "ACTIVE"
    STATUS_EXITING = "EXITING"
    STATUS_EXITED = "EXITED"
    STATUS_FAILED = "FAILED"
    STATUS_ROLLED_BACK = "ROLLED_BACK"
    STATUS_CHOICES = (
        (STATUS_PLANNED, "Planned"),
        (STATUS_EXECUTING, "Executing"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_EXITING, "Exiting"),
        (STATUS_EXITED, "Exited"),
        (STATUS_FAILED, "Failed"),
        (STATUS_ROLLED_BACK, "Rolled Back"),
    )
    TRANSACTION_CHOICES = (
        ("BUY", "BUY"),
        ("SELL", "SELL"),
    )
    OPTION_TYPE_CHOICES = (
        ("CE", "CE"),
        ("PE", "PE"),
    )

    strategy_execution = models.ForeignKey('StrategyExecution', on_delete=models.CASCADE, related_name='legs')
    leg_name = models.CharField(max_length=100)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_CHOICES)
    option_type = models.CharField(max_length=2, choices=OPTION_TYPE_CHOICES)
    strike_price = models.DecimalField(max_digits=12, decimal_places=2)
    symbol = models.CharField(max_length=255)
    token = models.CharField(max_length=100, null=True, blank=True)
    lot_size = models.IntegerField(default=0)
    quantity = models.IntegerField(default=0)
    order_type = models.CharField(max_length=20, null=True, blank=True)
    limit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    broker_order_id = models.CharField(max_length=255, null=True, blank=True)
    entry_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    exit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLANNED)
    pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    stop_loss = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    exchange = models.CharField(max_length=20, default="NFO")
    order_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.strategy_execution_id}:{self.leg_name}"


class StrategyExecutionLog(models.Model):
    strategy_execution = models.ForeignKey('StrategyExecution', on_delete=models.CASCADE, related_name='logs')
    event_type = models.CharField(max_length=100)
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.strategy_execution_id}:{self.event_type}"
class GroupService(models.Model):
    group_name = models.CharField(max_length=100)
    segment = models.ForeignKey(Segment, on_delete=models.SET_NULL, null=True, blank=True, related_name='group_Segments')
    # description = models.TextField(null=True, blank=True)
    Strategy = models.ManyToManyField("Strategies", related_name='client_Group_service_strategy', blank=True)
    json_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True)
    def __str__(self):
        return self.group_name    
class Broker(models.Model):
    broker_name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.broker_name

class TradeLog(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trade_logs')
    trade_setting = models.ForeignKey("ClientTradeSetting", on_delete=models.CASCADE, related_name='trade_logs')
    symbol = models.CharField(max_length=50,null=True, blank=True)
    is_trade_status = models.BooleanField(null=True, blank=True)
    trade_date = models.DateTimeField(default=get_ist_time)

    def __str__(self):
        return f"Trade log for {self.client.firstName} - {self.symbol} - {self.trade_date}"
class TradingLog(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True,null=True, blank=True)
    symbol = models.CharField(max_length=50,null=True, blank=True)
    strategy = models.CharField(max_length=50,null=True, blank=True)
class ClientTradeSetting(models.Model):
    ORDER_TYPE_CHOICES = (
        ("MARKET", "MARKET"),
        ("LIMIT", "LIMIT"),
    )

    client = models.ForeignKey('User', on_delete=models.CASCADE, null=True, blank=True)
    segment = models.ForeignKey('Segment', on_delete=models.CASCADE, null=True, blank=True)
    sub_segment = models.ForeignKey('SubSegment',on_delete=models.CASCADE, null=True, blank=True)
  
    # Specific trade settings for the selected segment/sub-segment
    symbol = models.CharField(max_length=50,null=True, blank=True)
    strategy = models.CharField(max_length=50,null=True, blank=True)
    broker = models.CharField(max_length=50,null=True, blank=True)
    product_type = models.CharField(max_length=20,null=True, blank=True)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default="LIMIT", null=True, blank=True)
    buffer_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    buy_sell = models.CharField(max_length=10, null=True, blank=True)  # "Buy" or "Sell"
    quantity = models.IntegerField(null=True, blank=True)
    trade_limit = models.IntegerField(null=True, blank=True)
    max_loss_for_day = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    min_loss_for_day = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    max_profit_for_day = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    min_profit_for_day = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    current_date = models.DateTimeField(auto_now_add=True)
    group_service =  models.CharField(max_length=255, null=True, blank=True)
    # Allow manual input for expiry_date, not auto field
    expiry_date = models.DateTimeField(null=True, blank=True)  # Allows manual input (client-defined)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    # Corrected 'is_tread_status' field definition
    is_tread_status = models.BooleanField(default=False)  # Default  False 
    sl_type=models.CharField(max_length=50, null=True, blank=True)
    stop_loss=models.IntegerField( null=True, blank=True)
    target=models.IntegerField( null=True, blank=True)
    def __str__(self):
        return f"Trade Setting {self.segment.name}"
class ClientBrokerdetails(models.Model):
    client = models.ForeignKey('User', on_delete=models.CASCADE,null=True, blank=True)
    broker_name =models.ForeignKey(Broker, on_delete=models.CASCADE,null=True, blank=True)
    execution_node = models.ForeignKey(
        'ExecutionNode',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='broker_details',
    )
    broker_API_SKEY = models.CharField(max_length=250,null=True, blank=True)
    broker_API_KEY = models.CharField(max_length=250,null=True, blank=True)
    broker_API_UID = models.CharField(max_length=50,null=True, blank=True)
    broker_Demate_User_Name = models.CharField(max_length=50,null=True, blank=True)
    broker_Totp_Authcode=models.CharField(max_length=250,null=True, blank=True)
    broker_pass=models.CharField(max_length=50,null=True, blank=True)
    
    # Buffer settings for limit orders (per compliance requirements)
    buffer_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=2.50,
        null=True,
        blank=True,
        help_text="Buffer percentage for limit orders (0.1 to 10.0). Default: 2.5%"
    )
    enable_market_orders = models.BooleanField(
        default=False,
        help_text="Market orders are disabled by default for compliance"
    )
    
    # New fields for token management
    request_token = models.TextField(null=True, blank=True)  # Temporary request token
    access_token = models.TextField(null=True, blank=True)
    refreshToken = models.TextField(null=True, blank=True)
    feed_token = models.TextField(null=True, blank=True)
    access_token_expiry = models.DateTimeField(null=True, blank=True)  # Expiry of the access token (if applicable)
    isTokenExpired=models.BooleanField(default=False,null=True, blank=True)
    tokenCreatedAt=models.DateTimeField(auto_now_add=True,null=True, blank=True)
    encrypted_broker_api_secret = models.TextField(null=True, blank=True)
    encrypted_broker_password = models.TextField(null=True, blank=True)
    encrypted_broker_totp_secret = models.TextField(null=True, blank=True)
    encrypted_access_token = models.TextField(null=True, blank=True)
    encrypted_refresh_token = models.TextField(null=True, blank=True)
    encrypted_feed_token = models.TextField(null=True, blank=True)
    broker_last_logout_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Trade Setting {self.broker_name} - {self.broker_API_SKEY}"

    def is_angel_one_broker(self) -> bool:
        return bool(
            self.broker_name
            and self.broker_name.broker_name
            and normalize_broker_name(self.broker_name.broker_name) == "angel one"
        )

    def get_canonical_client_code(self) -> str:
        return (self.broker_Demate_User_Name or self.broker_API_UID or "").strip()

    def _get_secret(self, field_name: str):
        return decrypt_value(getattr(self, field_name, None))

    def _set_secret(self, field_name: str, value) -> None:
        setattr(self, field_name, encrypt_value(value))

    def _normalize_secret_input(self, value):
        if isinstance(value, str):
            value = value.strip()
        return value or None

    def get_broker_api_secret(self):
        return self._get_secret("encrypted_broker_api_secret")

    def set_broker_api_secret(self, value) -> None:
        self._set_secret("encrypted_broker_api_secret", self._normalize_secret_input(value))
        if self.is_angel_one_broker():
            self.broker_API_SKEY = None

    def get_broker_password(self):
        secret = self._get_secret("encrypted_broker_password")
        if isinstance(secret, str):
            secret = secret.strip()
        if secret:
            return secret

        legacy = self.broker_pass
        if isinstance(legacy, str):
            legacy = legacy.strip()
        return legacy or None

    def set_broker_password(self, value) -> None:
        self._set_secret("encrypted_broker_password", self._normalize_secret_input(value))
        if self.is_angel_one_broker():
            self.broker_pass = None

    def get_broker_totp_secret(self):
        secret = self._get_secret("encrypted_broker_totp_secret")
        if isinstance(secret, str):
            secret = secret.strip()
        if secret:
            return secret

        legacy = self.broker_Totp_Authcode
        if isinstance(legacy, str):
            legacy = legacy.strip()
        return legacy or None

    def get_angel_one_login_credentials(self):
        client_code = self.get_canonical_client_code()
        if isinstance(client_code, str):
            client_code = client_code.strip()

        api_key = self.broker_API_KEY
        if isinstance(api_key, str):
            api_key = api_key.strip()

        return {
            "client_code": client_code or None,
            "api_key": api_key or None,
            "password": self.get_broker_password(),
            "totp_secret": self.get_broker_totp_secret(),
        }

    def set_broker_totp_secret(self, value) -> None:
        self._set_secret("encrypted_broker_totp_secret", self._normalize_secret_input(value))
        if self.is_angel_one_broker():
            self.broker_Totp_Authcode = None

    def _promote_angel_one_credentials(self):
        promoted_fields = set()
        if not self.is_angel_one_broker():
            return promoted_fields

        raw_api_secret = self._normalize_secret_input(self.broker_API_SKEY)
        raw_password = self._normalize_secret_input(self.broker_pass)
        raw_totp_secret = self._normalize_secret_input(self.broker_Totp_Authcode)

        if raw_api_secret:
            self.set_broker_api_secret(raw_api_secret)
            promoted_fields.update({"encrypted_broker_api_secret", "broker_API_SKEY"})
        elif self.broker_API_SKEY != raw_api_secret:
            self.broker_API_SKEY = raw_api_secret
            promoted_fields.add("broker_API_SKEY")

        if raw_password:
            self.set_broker_password(raw_password)
            promoted_fields.update({"encrypted_broker_password", "broker_pass"})
        elif self.broker_pass != raw_password:
            self.broker_pass = raw_password
            promoted_fields.add("broker_pass")

        if raw_totp_secret:
            self.set_broker_totp_secret(raw_totp_secret)
            promoted_fields.update({"encrypted_broker_totp_secret", "broker_Totp_Authcode"})
        elif self.broker_Totp_Authcode != raw_totp_secret:
            self.broker_Totp_Authcode = raw_totp_secret
            promoted_fields.add("broker_Totp_Authcode")

        return promoted_fields

    def get_access_token_secure(self):
        return self._get_secret("encrypted_access_token")

    def get_refresh_token_secure(self):
        return self._get_secret("encrypted_refresh_token")

    def get_feed_token_secure(self):
        return self._get_secret("encrypted_feed_token")

    def set_session_tokens(
        self,
        access_token,
        refresh_token=None,
        feed_token=None,
        expiry=None,
        mark_token_created: bool = False,
    ) -> None:
        self._set_secret("encrypted_access_token", access_token)
        self._set_secret("encrypted_refresh_token", refresh_token)
        self._set_secret("encrypted_feed_token", feed_token)
        if self.is_angel_one_broker():
            self.access_token = None
            self.refreshToken = None
            self.feed_token = None
        self.access_token_expiry = expiry
        self.isTokenExpired = not bool(access_token)
        if mark_token_created:
            self.tokenCreatedAt = timezone.now()

    def clear_session_tokens(self) -> None:
        self.set_session_tokens(None, None, None, expiry=None)
        self.request_token = None

    def mark_broker_logout(self) -> None:
        self.broker_last_logout_at = timezone.now()

    def clear_legacy_angel_sensitive_fields(self) -> None:
        if not self.is_angel_one_broker():
            return
        self.broker_pass = None
        self.broker_Totp_Authcode = None
        self.access_token = None
        self.refreshToken = None
        self.feed_token = None

    def save(self, *args, **kwargs):
        promoted_fields = self._promote_angel_one_credentials()
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and promoted_fields:
            kwargs["update_fields"] = list(set(update_fields).union(promoted_fields))
        super().save(*args, **kwargs)


class ExecutionNode(models.Model):
    EXECUTION_TYPE_VPS_NODE = "vps_node"
    EXECUTION_TYPE_PROXY = "proxy"
    EXECUTION_TYPE_CHOICES = [
        (EXECUTION_TYPE_VPS_NODE, "VPS Node"),
        (EXECUTION_TYPE_PROXY, "Proxy"),
    ]
    PROXY_PROTOCOL_HTTP = "http"
    PROXY_PROTOCOL_HTTPS = "https"
    PROXY_PROTOCOL_SOCKS5 = "socks5"
    PROXY_PROTOCOL_CHOICES = [
        (PROXY_PROTOCOL_HTTP, "HTTP"),
        (PROXY_PROTOCOL_HTTPS, "HTTPS"),
        (PROXY_PROTOCOL_SOCKS5, "SOCKS5"),
    ]
    STATUS_FREE = "free"
    STATUS_ASSIGNED = "assigned"
    STATUS_ONLINE = "online"
    STATUS_OFFLINE = "offline"
    STATUS_MAINTENANCE = "maintenance"
    STATUS_DISABLED = "disabled"
    STATUS_CHOICES = [
        (STATUS_FREE, "Free"),
        (STATUS_ASSIGNED, "Assigned"),
        (STATUS_ONLINE, "Online"),
        (STATUS_OFFLINE, "Offline"),
        (STATUS_MAINTENANCE, "Maintenance"),
        (STATUS_DISABLED, "Disabled"),
    ]

    name = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField(unique=True)
    provider = models.CharField(max_length=150, blank=True, null=True)
    execution_type = models.CharField(max_length=20, choices=EXECUTION_TYPE_CHOICES, default=EXECUTION_TYPE_VPS_NODE, db_index=True)
    server_url = models.URLField(max_length=500, blank=True, null=True)
    node_id = models.CharField(max_length=120, unique=True, blank=True, null=True)
    node_secret = models.TextField(blank=True, null=True)
    proxy_host = models.CharField(max_length=255, blank=True, null=True)
    proxy_port = models.PositiveIntegerField(blank=True, null=True)
    proxy_username = models.CharField(max_length=255, blank=True, null=True)
    proxy_password = models.TextField(blank=True, null=True)
    proxy_protocol = models.CharField(max_length=20, choices=PROXY_PROTOCOL_CHOICES, blank=True, null=True)
    proxy_public_ip_verified = models.BooleanField(default=False)
    proxy_last_verified_at = models.DateTimeField(null=True, blank=True)
    proxy_last_seen_ip = models.GenericIPAddressField(null=True, blank=True)
    proxy_last_error = models.TextField(blank=True, null=True)
    assigned_client = models.OneToOneField(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='execution_node',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_FREE, db_index=True)
    is_active = models.BooleanField(default=True)
    is_verified_with_broker = models.BooleanField(default=False)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    last_seen_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["assigned_client"]),
            models.Index(fields=["execution_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.ip_address})"

    def set_node_secret(self, secret) -> None:
        self.node_secret = encrypt_value(str(secret or "").strip() or None)

    def get_node_secret(self):
        return decrypt_value(self.node_secret) or self.node_secret

    def set_proxy_password(self, password) -> None:
        self.proxy_password = encrypt_value(str(password or "").strip() or None)

    def get_proxy_password(self):
        return decrypt_value(self.proxy_password) or self.proxy_password

    def clean(self):
        super().clean()
        if self.execution_type == self.EXECUTION_TYPE_PROXY:
            missing = []
            if not self.ip_address:
                missing.append("ip_address")
            if not self.proxy_host:
                missing.append("proxy_host")
            if not self.proxy_port:
                missing.append("proxy_port")
            if not self.proxy_protocol:
                missing.append("proxy_protocol")
            if missing:
                from django.core.exceptions import ValidationError

                raise ValidationError({field: "Required for proxy execution nodes." for field in missing})
        else:
            missing = []
            if not self.server_url:
                missing.append("server_url")
            if not self.node_id:
                missing.append("node_id")
            if not self.node_secret:
                missing.append("node_secret")
            if missing:
                from django.core.exceptions import ValidationError

                raise ValidationError({field: "Required for VPS execution nodes." for field in missing})

    def mark_log(self, event_type, message, *, client=None, metadata=None):
        return ExecutionNodeLog.objects.create(
            execution_node=self,
            client=client,
            event_type=event_type,
            message=message,
            metadata=metadata or {},
        )


class ExecutionOrderJob(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SENT_TO_NODE = "sent_to_node"
    STATUS_ACCEPTED_BY_NODE = "accepted_by_node"
    STATUS_PLACED = "placed"
    STATUS_REJECTED = "rejected"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    STATUS_PROXY_ROUTING = "proxy_routing"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SENT_TO_NODE, "Sent to node"),
        (STATUS_ACCEPTED_BY_NODE, "Accepted by node"),
        (STATUS_PROXY_ROUTING, "Proxy routing"),
        (STATUS_PLACED, "Placed"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    client = models.ForeignKey('User', on_delete=models.CASCADE, related_name='execution_order_jobs')
    broker_details = models.ForeignKey('ClientBrokerdetails', on_delete=models.SET_NULL, null=True, blank=True, related_name='execution_order_jobs')
    execution_node = models.ForeignKey(ExecutionNode, on_delete=models.PROTECT, related_name='order_jobs')
    execution_type = models.CharField(max_length=20, choices=ExecutionNode.EXECUTION_TYPE_CHOICES, default=ExecutionNode.EXECUTION_TYPE_VPS_NODE, db_index=True)
    symbol = models.CharField(max_length=255, null=True, blank=True)
    token = models.CharField(max_length=255, null=True, blank=True)
    exchange = models.CharField(max_length=50, null=True, blank=True)
    product = models.CharField(max_length=50, null=True, blank=True)
    order_type = models.CharField(max_length=50, null=True, blank=True)
    transaction_type = models.CharField(max_length=50, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    trigger_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    request_payload = models.JSONField(default=dict, blank=True)
    node_response = models.JSONField(null=True, blank=True)
    broker_response = models.JSONField(null=True, blank=True)
    proxy_metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(null=True, blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    idempotency_key = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["execution_node"]),
            models.Index(fields=["client"]),
            models.Index(fields=["status"]),
            models.Index(fields=["execution_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.idempotency_key} - {self.status}"


class ExecutionNodeLog(models.Model):
    execution_node = models.ForeignKey(ExecutionNode, on_delete=models.CASCADE, related_name='logs')
    client = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='execution_node_logs')
    event_type = models.CharField(max_length=80, db_index=True)
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["execution_node"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type}: {self.execution_node_id}"
    
class Tradeorderhistory(models.Model):
    client = models.ForeignKey('User', on_delete=models.CASCADE)
    GroupService =  models.CharField(max_length=255, null=True, blank=True)
    date = models.DateField(auto_now_add=True, null=True, blank=True)
    trading_symbol = models.CharField(max_length=255, null=True, blank=True)
    Index_Symbol    = models.CharField(max_length=255, null=True, blank=True)
    order_id = models.CharField(max_length=255, null=True, blank=True)  # Changed to CharField for order ID, it could be alphanumeric
    order_status = models.CharField(max_length=50, null=True, blank=True)
    response_data = models.JSONField(null=True, blank=True)  # Store the full response as JSON
    failure_reason = models.TextField(null=True, blank=True)  # Store failure reason if any
    broker=models.CharField(max_length=255, null=True, blank=True)
    order_params= models.JSONField(null=True, blank=True) 
    transaction_type=models.CharField(max_length=50, null=True, blank=True)#BUY,Sell
    #add this fileds
    strategy=models.CharField(max_length=50, null=True, blank=True)
    Entry_type=models.CharField(max_length=50, null=True, blank=True)#but or sell LE/LX
    Exit_type=models.CharField(max_length=50, null=True, blank=True)#but or sell LE/LX
    Entry_Price=models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    Exit_Price=models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    SignalEntry_time=models.DateTimeField(auto_now_add=True,null=True, blank=True)
    SignalExit_time=models.DateTimeField(null=True, blank=True)
    Exchange=models.CharField(max_length=50, null=True, blank=True)
    Segment=models.CharField(max_length=50, null=True, blank=True)
    Lot=models.IntegerField(null=True, blank=True)
    LivePrice=models.DecimalField(max_digits=15, decimal_places=2,null=True, blank=True)
    Entry_status=models.CharField(max_length=50, null=True, blank=True)
    Exit_status=models.CharField(max_length=50, null=True, blank=True)
    Total=models.DecimalField(max_digits=15, decimal_places=2,null=True, blank=True)
    webhook_signal= models.JSONField(null=True, blank=True) 
    EntryQty=models.IntegerField( null=True, blank=True)
    ExitQty=models.IntegerField( null=True, blank=True)
    trade_order_status = models.CharField(max_length=15, null=True, blank=True)
    history_id = models.CharField(max_length=100, unique=True, null=True, blank=True)

    def __str__(self):
        return f"Order ID: {self.order_id}"
class CompanyProfileDetails(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="company_profile",null=True, blank=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company_email = models.EmailField(unique=True, blank=True, null=True)
    company_support_email = models.EmailField(unique=True, blank=True, null=True)
    company_phone_number = models.BigIntegerField(unique=True, blank=True, null=True)  
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    login_link = models.URLField(blank=True, null=True)  # Assuming this is a URL
    help_center_link = models.URLField(blank=True, null=True)  # Assuming this is a URL
    company_website = models.URLField(blank=True, null=True)  # Assuming this is a URL
    company_sender_name = models.CharField(max_length=255, blank=True, null=True)
    company_favicon=models.ImageField(upload_to='company_favicon/', blank=True, null=True)
    def __str__(self):
        return self.company_name if self.company_name else "Unnamed Company"
class WebsocketDetails(models.Model):
    Auth_token = models.TextField(blank=True, null=True) 
    token_status= models.CharField(max_length=255, blank=True, null=True)
    expiry_time = models.DateTimeField( blank=True, null=True)
    def __str__(self):
        return f"Auth_token: {self.Auth_token}"

class CompanySmtpDetails(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="company_smtp",null=True, blank=True)  # Changed related_name
    email_host = models.CharField(max_length=255, blank=True, null=True)
    email_port = models.PositiveIntegerField(blank=True, null=True)
    email_use_tls = models.BooleanField(default=True)
    email_host_user = models.EmailField(blank=True, null=True)
    email_host_password = models.CharField(max_length=255, blank=True, null=True)
    default_from_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.email_host if self.email_host else "SMTP Configuration"


PAYMENT_METHOD_CHOICES = [
    ('UPI', 'UPI Scanner'),
    ('CARD', 'Credit Card'),
    ('QR', 'QR Code'),
]

class AdminLicense(models.Model):
    sub_admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="admin_license", null=True, blank=True)
    license_qty = models.IntegerField(null=True, blank=True)  
    license_price = models.IntegerField(null=True, blank=True) 
    total_amount = models.IntegerField(null=True, blank=True) 
    is_active = models.BooleanField(default=False)  # Becomes True when payment is successful
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.license_qty and self.license_price:
            self.total_amount = self.license_qty * self.license_price
        super(AdminLicense, self).save(*args, **kwargs)

    def __str__(self):
        return f"License for {self.sub_admin.fullName if self.sub_admin else 'No Sub Admin'}"

class Payment(models.Model):
    sub_admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments", null=True, blank=True)
    license = models.ForeignKey(AdminLicense, on_delete=models.CASCADE, related_name="payments", null=True, blank=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)  
    payment_status = models.BooleanField(default=False)  # True if payment is successful
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=256, null=True, blank=True)
    upi_id = models.CharField(max_length=100, null=True, blank=True)  # Removed unique=True

    def __str__(self):
        return f"Payment {self.razorpay_order_id} - {'Success' if self.payment_status else 'Pending'}"
