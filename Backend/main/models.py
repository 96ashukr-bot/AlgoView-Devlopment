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
from pytz import timezone
def get_ist_time():
    # Convert the current UTC time to IST
    ist_timezone = timezone('Asia/Kolkata')
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
        # # Ensure role is a Role instance and is active
        # role = extra_fields.get('role')
        # if isinstance(role, int):
        #     role = Role.objects.get(id=role)
        # elif not isinstance(role, Role):
        #     raise ValueError(_('Invalid Role instance'))

        # if role and role.status != Role.ACTIVE:
        #     raise ValueError(_('Only active roles can be assigned to users'))

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
    email = models.EmailField(unique=True)
    phoneNumber = models.CharField(max_length=15, null=True, blank=True)
    firstName = models.CharField(max_length=150)
    middleName = models.CharField(max_length=150,null=True,blank=True)
    lastName = models.CharField(max_length=150,blank=True,null=True)
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
        """Calculate start_date_client and end_date_client based on to_month."""
        today = datetime.today()
                
        license_type = getattr(self.license, 'name', None)  # Modify 'name' to match your actual attribute

        if license_type == "Live":
            print("Inside Live license section")
            if self.to_month:
                print("inside to month......")
                try:
                    if self.to_month:
                        months = int(self.to_month)
                        self.start_date_client = today.date()
                        self.end_date_client = (today + relativedelta(months=months)).date()
                    # elif "day" in self.to_month:
                    #     days = int(self.to_month.split()[0])
                    #     self.start_date_client = today.date()
                    #     self.end_date_client = (today + timedelta(days=days)).date()
                    else:
                        # Handle unexpected format by setting dates to None
                        self.start_date_client = None
                        self.end_date_client = None
                except ValueError:
                    # Handle invalid integer conversion
                    self.start_date_client = None
                    self.end_date_client = None
            else:
                # If no to_month provided, set dates to None
                self.start_date_client = None
                self.end_date_client = None

        elif license_type == "Demo":
            print("Inside Demo license section")
            # Retain the provided start and end dates as is
            # If you don't need to assign dates, just omit these lines
            self.start_date_client = self.start_date_client
            self.end_date_client = self.end_date_client
                
            
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
    last_login_time = models.DateTimeField()
    last_logout_time = models.DateTimeField(null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)  # Store session key for reference
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.email} - {self.last_login_time}'

    def mark_logout(self):
        """ Marks logout time when the user logs out """
        self.logout_time = get_ist_time()
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
    name = models.CharField(max_length=150)
    Lots=models.IntegerField(blank=True,null=True)
    segment = models.ForeignKey(Segment, on_delete=models.SET_NULL, null=True, blank=True, related_name='strategy_segments')
    category = models.ForeignKey(categories, on_delete=models.SET_NULL, null=True, blank=True, related_name='strategy_categories')
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
class GroupService(models.Model):
    group_name = models.CharField(max_length=100)
    segment = models.ForeignKey(Segment, on_delete=models.SET_NULL, null=True, blank=True, related_name='group_Segments')
    # description = models.TextField(null=True, blank=True)
    # service_count=
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
    client = models.ForeignKey('User', on_delete=models.CASCADE, null=True, blank=True)
    segment = models.ForeignKey('Segment', on_delete=models.CASCADE, null=True, blank=True)
    sub_segment = models.ForeignKey('SubSegment',on_delete=models.CASCADE, null=True, blank=True)
  
    # Specific trade settings for the selected segment/sub-segment
    symbol = models.CharField(max_length=50,null=True, blank=True)
    strategy = models.CharField(max_length=50,null=True, blank=True)
    broker = models.CharField(max_length=50,null=True, blank=True)
    product_type = models.CharField(max_length=20,null=True, blank=True)
    
    buy_sell = models.CharField(max_length=10, null=True, blank=True)  # "Buy" or "Sell"
    quantity = models.IntegerField(null=True, blank=True)
    trade_limit = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    max_loss_for_day = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    min_loss_for_day = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    max_profit_for_day = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    min_profit_for_day = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    current_date = models.DateTimeField(auto_now_add=True)
    
    # Allow manual input for expiry_date, not auto field
    expiry_date = models.DateTimeField(null=True, blank=True)  # Allows manual input (client-defined)

    # Corrected 'is_tread_status' field definition
    is_tread_status = models.BooleanField(default=True)  # Default to True or False as required
    
    def __str__(self):
        return f"Trade Setting {self.segment.name} - {self.sub_segment.name}"
class ClientBrokerdetails(models.Model):
    client = models.ForeignKey('User', on_delete=models.CASCADE,null=True, blank=True)
    broker_name =models.ForeignKey(Broker, on_delete=models.CASCADE,null=True, blank=True)
    broker_API_SKEY = models.CharField(max_length=250,null=True, blank=True)
    broker_API_KEY = models.CharField(max_length=250,null=True, blank=True)
    broker_API_UID = models.CharField(max_length=50,null=True, blank=True)
    broker_Demate_User_Name = models.CharField(max_length=50,null=True, blank=True)
    broker_Totp_Authcode=models.CharField(max_length=250,null=True, blank=True)
    broker_pass=models.CharField(max_length=50,null=True, blank=True)
    # New fields for token management
    request_token = models.CharField(max_length=250, null=True, blank=True)  # Temporary request token
    access_token = models.CharField(max_length=500, null=True, blank=True)  # Persistent access token
    access_token_expiry = models.DateTimeField(null=True, blank=True)  # Expiry of the access token (if applicable)
    
    
    def __str__(self):
        return f"Trade Setting {self.broker_name} - {self.broker_API_SKEY}"
    
class Tradeorderhistory(models.Model):
    client = models.ForeignKey('User', on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True, null=True, blank=True)
    trading_symbol = models.CharField(max_length=255, null=True, blank=True)
    Index_Symbol    = models.CharField(max_length=255, null=True, blank=True)
    order_id = models.CharField(max_length=255, null=True, blank=True)  # Changed to CharField for order ID, it could be alphanumeric
    order_status = models.CharField(max_length=15, null=True, blank=True)
    response_data = models.JSONField(null=True, blank=True)  # Store the full response as JSON
    failure_reason = models.TextField(null=True, blank=True)  # Store failure reason if any
    broker=models.CharField(max_length=255, null=True, blank=True)
    order_params= models.JSONField(null=True, blank=True) 
    
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
    def __str__(self):
        return f"Order ID: {self.order_id}, Status: {self.order_status}"
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

    def __str__(self):
        return self.company_name if self.company_name else "Unnamed Company"


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
