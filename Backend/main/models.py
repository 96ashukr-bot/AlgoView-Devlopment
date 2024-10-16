import datetime
import random
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class Role(models.Model):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    
    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=ACTIVE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
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
    lastName = models.CharField(max_length=150,blank=True)
    fullName = models.CharField(max_length=300, blank=True, editable=False)  # Will be automatically generated
    profilePicture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE,null=True, blank=True)
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
    
    # Current Address Fields
    current_add_line_1 = models.CharField(max_length=255, null=True, blank=True)
    current_add_line_2 = models.CharField(max_length=255, null=True, blank=True)
    current_city = models.CharField(max_length=100, null=True, blank=True)
    current_state = models.CharField(max_length=50, null=True, blank=True)
    current_country = models.CharField(max_length=20, null=True, blank=True)
    current_zip_code = models.CharField(max_length=20, null=True, blank=True)

    external_user = models.CharField(max_length=50, null=True, blank=True)
    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['firstName','lastName', 'phoneNumber']

    def __str__(self):
        return self.email

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.firstName} {self.lastName}"

    def get_short_name(self):
        return self.firstName

    def save(self, *args, **kwargs):
        self.fullName = f"{self.firstName} {self.lastName}"
        super().save(*args, **kwargs)

class KYC(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE,blank=True, null=True)
    id_proof = models.CharField(max_length=50)
    document_file_front = models.FileField(upload_to='kyc_documents/front/', blank=True)
    document_file_back = models.FileField(upload_to='kyc_documents/back/', blank=True)
    is_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # Add status field
    verified_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='verified_kyc')  # Admin who verified
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    # New fields
    address_proof_id = models.CharField(max_length=100, blank=True)  # To store address ID or code
    address_prof_front = models.FileField(upload_to='kyc_documents/address_front/', blank=True)  # Address proof front
    address_prof_back = models.FileField(upload_to='kyc_documents/address_back/', blank=True)  # Address proof back
  
    
class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)

    def generate_otp(self):
        self.otp_code = random.randint(100000, 999999)
        self.expires_at = timezone.now() + datetime.timedelta(seconds=120)  # Set expiration to 120 seconds from now
        self.is_verified = False
        self.save()
        
    def is_expired(self):
        return timezone.now() > self.expires_at if self.expires_at else True
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
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permissions = models.ManyToManyField(Permission, related_name="role_permissions", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.role.name} - Permissions" 
    
class OrderLog(models.Model):
    signal_time = models.DateTimeField()  # Time of the signal
    order_type = models.CharField(max_length=10)  # 'LX' or 'LE' (Type)
    symbol = models.CharField(max_length=100)  # Symbol (e.g., BANKNIFTY)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price
    strategy = models.CharField(max_length=100)  # Strategy (e.g., Support & Resistance)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default="Pending")  # "Success", "Failed"
    failure_reason = models.TextField(null=True, blank=True)  # Reason for failure (optional)
    def __str__(self):
        return f"{self.signal_time} - {self.order_type} - {self.symbol} - {self.price}"   
    
class UserActivityLog(models.Model):
    ACTION_TYPES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES)
    last_login_time = models.DateTimeField()
    last_logout_time = models.DateTimeField(null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)  # Store session key for reference
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.email} - {self.last_login_time}'

    def mark_logout(self):
        """ Marks logout time when the user logs out """
        self.logout_time = timezone.now()
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
    state_id = models.ForeignKey( State,related_name='cities', on_delete=models.CASCADE)
    state_code = models.TextField(null=True, blank=True)


    def __str__(self):
        return self.name
    
class License(models.Model):
    name=models.CharField(max_length=255,null=True)    
    no_of_days_month=models.IntegerField(blank=True,null=True)
    period=models.CharField(max_length=255,null=True) 
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
class Services(models.Model):
    service_name = models.CharField(max_length=100)
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name='service_segments',blank=True)
    category= models.ForeignKey(categories, on_delete=models.CASCADE,related_name='services_categories',blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.service_name
class Strategies(models.Model):
    name = models.CharField(max_length=150)
    Lots=models.IntegerField(blank=True,null=True)
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name='strategy_segments',blank=True,null=False)
    category= models.ForeignKey(categories, on_delete=models.CASCADE,related_name='strategy_categories', blank=False, null=False)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_submit= models.BooleanField(default=True)
    Indicator=models.ImageField(upload_to='strategy/Indicator', null=True, blank=True)
    Strategy_Tester=models.ImageField(upload_to='strategy/Strategy_Tester', null=True, blank=True)
    Strategy_Logo=models.ImageField(upload_to='strategy/Strategy_Logo', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True)
    
    # Pricing Options
    monthly_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quarterly_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    half_yearly_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    yearly_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.name
class GroupService(models.Model):
    group_name = models.CharField(max_length=100)
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name='group_Segments',blank=True,null=True)
    # description = models.TextField(null=True, blank=True)
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


    