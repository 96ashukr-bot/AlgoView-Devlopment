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
    def create_user(self, email, username, phone_number, role, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        
        # Ensure role is a Role instance and is active
        if isinstance(role, int):
            role = Role.objects.get(id=role)
        elif not isinstance(role, Role):
            raise ValueError(_('Invalid Role instance'))

        if role.status != Role.ACTIVE:
            raise ValueError(_('please select active role to create user'))

        user = self.model(email=email, username=username, phone_number=phone_number, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db) 
        return user

    def create_superuser(self, email, username, phone_number, role, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        return self.create_user(email, username, phone_number, role, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'phone_number', 'role']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

class KYC(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=50)
    document_file = models.FileField(upload_to='kyc_documents/', null=True, blank=True)
    confirmation = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"KYC for {self.user.email} - {self.document_type}"
    
class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)

    def generate_otp(self):
        self.otp_code = random.randint(100000, 999999)
        self.save()
    
    def __str__(self):
        return f"{self.user.email} OTP"

