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
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    # UserName = models.CharField(max_length=150, null=True, blank=True)
    # Date_Of_Birth = models.DateField(default=datetime.date(2000, 1, 1))
    # email = models.EmailField(blank=True)
    # phone = models.CharField(max_length=15)
    document_type = models.CharField(max_length=50)
    document_file_front = models.FileField(upload_to='kyc_documents/front/', blank=True)
    document_file_back = models.FileField(upload_to='kyc_documents/back/', blank=True)
    is_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # Add status field
    verified_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='verified_kyc')  # Admin who verified
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"KYC for {self.email} - {self.document_type}"    
    
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
    def __str__(self):
        return f"{self.signal_time} - {self.order_type} - {self.symbol} - {self.price}"       
# class TradeLog(models.Model):
#     data_type = models.CharField(max_length=20)  # e.g., option or future
#     alert_key = models.CharField(max_length=50)  # Unique alert key
#     action = models.CharField(max_length=10)     # buy or sell
#     symbol = models.CharField(max_length=20)     # e.g., NIFTY
#     expiry = models.DateField()                  # Expiry date for the option
#     strike_price = models.FloatField()           # Strike price of the option
#     option_type = models.CharField(max_length=5) # CE (Call) or PE (Put)
#     lot = models.IntegerField()                  # Number of lots
#     order_type = models.CharField(max_length=20) # e.g., MARKET or LIMIT
#     product_type = models.CharField(max_length=20)  # e.g., NRML
#     strategy_tag = models.CharField(max_length=50)  # Tag for the strategy
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.action} {self.symbol} {self.expiry} {self.strike_price} {self.option_type}"
    