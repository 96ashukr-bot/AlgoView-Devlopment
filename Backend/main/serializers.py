from django.forms import ValidationError
import requests
from rest_framework import serializers
from main.tasks import send_email_async, send_email_pass_async
from .models import *
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from rest_framework.validators import UniqueValidator
from main.email import EmailService
support_email=settings.DEFAULT_FROM_EMAIL
contact_number=settings.CONTACT_NUM
login_link=settings.LOGIN_LINK
help_center_link=settings.HELP_CENTER_LINK
company_website=settings.COMPANY_WEBSITE    
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name','status']

class UserAssignRoleSerializer(serializers.ModelSerializer):
    role_id = serializers.IntegerField(write_only=True)
    role = RoleSerializer(read_only=True)  # Use the RoleSerializer to return role details

    class Meta:
        model = User
        fields = ['id', 'email', 'firstName', 'lastName', 'role', 'role_id']

    def update(self, instance, validated_data):
        # Fetch role by role_id and assign it to the user
        role_id = validated_data.pop('role_id', None)
        if role_id:
            role = Role.objects.get(id=role_id)
            instance.role = role
        return super().update(instance, validated_data)
class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['id', 'email', 'firstName', 'lastName', 'phoneNumber', 'profilePicture', 'password']

    def validate_role(self, value):
        if value.status != Role.ACTIVE:
            raise serializers.ValidationError('The selected role is not active.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data, password=password)
        return user
# class UsergetSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['id', 'email', 'firstName', 'lastName', 'phoneNumber', 'profilePicture', 'role', 'is_active', 'is_staff']

    # def update(self, instance, validated_data):
    #     instance.email = validated_data.get('email', instance.email)
    #     instance.firstName = validated_data.get('firstName', instance.firstName)
    #     instance.lastName = validated_data.get('lastName', instance.lastName)
    #     instance.phoneNumber = validated_data.get('phoneNumber', instance.phoneNumber)
    #     instance.profilePicture = validated_data.get('profilePicture', instance.profilePicture)
    #     instance.role = validated_data.get('role', instance.role)
    #     instance.is_active = validated_data.get('is_active', instance.is_active)
    #     instance.is_staff = validated_data.get('is_staff', instance.is_staff)
    #     instance.save()
    #     return instance
class UserRegistrationSerializer(serializers.ModelSerializer):
    phoneNumber = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="Phone number already exists.")]
    )
    class Meta:
        model = User
        fields = ['email', 'firstName', 'lastName', 'phoneNumber', 'profilePicture', 'role']


    def create(self, validated_data):
        # Generate a random password
        password = get_random_string(length=12)

        # Start an atomic transaction
        with transaction.atomic():
            # Create the user with the generated password
            user = User.objects.create_user(**validated_data, password=password, external_user='true')
            
            # Try to send the password to the user's email
            try:
                print("pass...",password)
                EmailService.send_password_email(user.email, password,user.firstName,login_link,support_email,help_center_link,company_website,contact_number)
            except Exception as e:
                # If email sending fails, delete the user and raise an exception
                user.delete()
                raise serializers.ValidationError(f"Error sending email: {str(e)}")
        
        return user
class UserRegistrationSerializer_sync(serializers.ModelSerializer):
    phoneNumber = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="Phone number already exists.")]
    )

    class Meta:
        model = User
        fields = ['email', 'firstName', 'lastName', 'phoneNumber', 'profilePicture', 'role']
    
    def create(self, validated_data):
        password = get_random_string(length=8)
        with transaction.atomic():
            user = User.objects.create_user(**validated_data, password=password)

            try:
                print("pass...",password)
                # Call the async task to send the email
                send_email_pass_async.delay(
                    user.email,
                    password,
                    user.firstName,
                    login_link,
                    support_email,
                    help_center_link,
                    company_website,
                    contact_number
                )
            except Exception as e:
                user.delete()
                raise serializers.ValidationError(f"Error sending email: {str(e)}")
        
        return user

class CustomLoginSerializer_sync(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        user = authenticate(email=email, password=password)
        
        if user is None:
            raise ValidationError('Invalid credentials email or password')
        
        # Check if the user is logging in with a temporary password
        if user.is_password_temporary:
            otp_instance, created = OTP.objects.get_or_create(user=user, is_verified=False)
            otp_instance.generate_otp()
            
            # Use Celery to send OTP asynchronously
            send_email_async.delay(
                subject='Your OTP Code',
                message=f'Your OTP code is {otp_instance.otp_code}.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email]
            )

            return {
                'message': f"OTP sent to your email: {email}. Please verify."
            }
        
        # Check if the user needs to change the temporary password
        if not user.is_new_password:
            return {
                'message': 'Please change your password as this is a one-time temporary password.'
            }
        else:
            otp_instance, created = OTP.objects.get_or_create(user=user, is_verified=False)
            otp_instance.generate_otp()
            
            # Use Celery to send OTP asynchronously
            send_email_async.delay(
                subject='Your OTP Code',
                message=f'Your OTP code is {otp_instance.otp_code}.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email]
            )
            return {
                'message': f"OTP sent to your email: {email}. Please verify."
            }
            
class CustomLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        user = authenticate(email=email, password=password)
        
        if user is None:
            raise serializers.ValidationError('Invalid credentials')
        if not user.role and user.external_user == "true" or user.role.name.lower() == 'client' :
                otp_instance, created = OTP.objects.get_or_create(user=user, is_verified=False)
                otp_instance.generate_otp()

                # Send OTP to user's email
                EmailService.send_login_email_otp(user.email, otp_instance.otp_code, user.firstName)

                return {
                    'message': f"OTP sent to your email: {email}. Please verify."
                }
        else:
            # If the user does not have the 'client' role, proceed with direct login
            if not user.is_new_password :
                message= 'Please change your password as this is a one-time temporary password.'
            else:
                message="login successfully"
            refresh = RefreshToken.for_user(user)
            request = self.context.get('request')  # Get the request context
            kyc_exists = KYC.objects.filter(user_id=user.id).exists()

            ekyc_status = kyc_exists  # True if KYC record exists, otherwise False
            # Save the new password
            if request:
                try:
                    public_ip = requests.get('https://api.ipify.org').text  # You can use other services like 'https://checkip.amazonaws.com/' too
                except requests.RequestException:
                    public_ip = None  # Handle the case when the request fails
                session_key = request.session.session_key if request.session else None
                # Log user's activity in the UserActivityLog model
                UserActivityLog.objects.create(
                    user=user,
                    action_type='login',
                    last_login_time=timezone.now(),
                    ip_address=public_ip,  # Store the client's IP address
                    session_key=session_key)

                return {
                    'user_id': user.id,
                    'message': message,
                    'email': user.email,
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'role': {
                        'role_id': user.role.id if user.role else None,
                        'role_name': user.role.name if user.role else None,
                        'role_status': user.role.status if user.role else None,
                    },
                    'ekyc_status': ekyc_status
                }

class CustomLoginSerializer_old(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        user = authenticate(email=email, password=password)
        if user is None:
            raise serializers.ValidationError('Invalid credentials')
        # Check if the user is logging in with a temporary password
        if  user.is_password_temporary:#password is not temporary
            # Generate OTP for email
            otp_instance, created = OTP.objects.get_or_create(user=user, is_verified=False)
            otp_instance.generate_otp()
        # Send OTP to email
            EmailService.send_login_email_otp(user.email, otp_instance.otp_code,user.firstName)

            return {
                'message': f"OTP sent to your email : {email}. Please verify "
            }
        else:
            otp_instance, created = OTP.objects.get_or_create(user=user, is_verified=False)
            otp_instance.generate_otp()
            if not user.is_new_password:
                return {
                    'message': 'Please change your password as this is a one-time temporary password.'
                }
            else:
                if user.is_new_password:
                    otp_instance, created = OTP.objects.get_or_create(user=user, is_verified=False)
                    otp_instance.generate_otp()
                    EmailService.send_login_email_otp(user.email, otp_instance.otp_code,user.firstName)
                    return {
                        'message': f"OTP sent to your email: {email}. Please verify."
                    }

    # def send_email_otp(self, email, otp_code):
    #     subject = 'Your OTP Code'
    #     message = f'Your OTP code is {otp_code}.'
    #     from_email = settings.DEFAULT_FROM_EMAIL
        # send_mail(subject, message, from_email, [email])


class ChangePasswordSerializer(serializers.Serializer):
    OldPassword = serializers.CharField(required=True, write_only=True)
    NewPassword = serializers.CharField(required=True, write_only=True)
    ConfirmNewPassword = serializers.CharField(required=True, write_only=True)
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is not correct.')
        return value
    def validate_new_password(self, value):
        # Add any custom password validation logic here if needed
        if len(value) < 8:
            raise serializers.ValidationError('New password must be at least 8 characters long.')
        return value
    def validate(self, data):
        new_password = data.get('NewPassword')
        confirm_password = data.get('ConfirmNewPassword')

        if new_password != confirm_password:
            raise serializers.ValidationError({'ConfirmNewPassword': 'New password and confirm password do not match.'})

        return data
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['NewPassword'])
        user.is_new_password=True
        user.save()
        return {
            'user_id': user.id,
            'email': user.email,
            'role': {
                'role_id': user.role.id if user.role else None,
                'role_name': user.role.name if user.role else None,
                'role_status': user.role.status if user.role else None,
            }
        }


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data.get('email')
        otp_code = data.get('otp_code')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid user')
        # Get the latest unverified OTP for the user
        otp_instance = OTP.objects.filter(user=user, is_verified=False).last()

        if not otp_instance:
            raise serializers.ValidationError('No OTP found. Please request a new one.')

        # Check if the OTP has expired
        if otp_instance.is_expired():
            raise serializers.ValidationError('OTP has expired. Please request a new one.')

        # Verify the OTP code
        if otp_instance.otp_code != otp_code:
            raise serializers.ValidationError('Invalid OTP.')

        # Mark OTP as verified
        otp_instance.is_verified = True
        otp_instance.save()
        # If OTP is verified, issue JWT tokens
        user.is_password_temporary = False
        user.save()
        refresh = RefreshToken.for_user(user)
        # Log user login activity after OTP verification
        request = self.context.get('request')  # Get the request context
        if request:
            try:
                public_ip = requests.get('https://api.ipify.org').text  # You can use other services like 'https://checkip.amazonaws.com/' too
            except requests.RequestException:
                public_ip = None  # Handle the case when the request fails
            session_key = request.session.session_key if request.session else None

            # Store login time in UserActivityLog
            UserActivityLog.objects.create(
                user=user,
                action_type='login',
                last_login_time=timezone.now(),
                ip_address=public_ip,
                session_key=session_key
            )
        if not user.is_new_password:
            message= 'Please change your password as this is a one-time temporary password.'
        else:
            message="login successfully"
        return {
            'user_id': user.id,  # Use ID instead of User object
            'email': user.email,  # You can add any other fields you nee
            'message':message,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'role': {
                'role_id': user.role.id if user.role else None,
                'role_name': user.role.name if user.role else None,
                'role_status': user.role.status if user.role else None,
            }
            
        }

class TokenSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    NewPassword = serializers.CharField()
    ConfirmPassword = serializers.CharField()

    def validate(self, data):
        NewPassword = data.get('NewPassword')
        ConfirmPassword = data.get('ConfirmPassword')

        if NewPassword != ConfirmPassword:
            raise serializers.ValidationError({'confirm_password': 'New password and confirm password do not match.'})

        return data


# Serializer for viewing the user profile
class UserProfileRetrieveSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['email', 'firstName', 'lastName','middleName', 'phoneNumber', 'profilePicture', 'PANEL_CLIENT_KEY', 
                  'start_date', 'end_date', 'client_type', 'Address_line1','Address_line2','City','State','Country','Zip_code','Permanent_address','Current_address' ,'role','is_enable']

    def get_role(self, obj):
        if obj.role:
            return {
                'id': obj.role.id,
                'name': obj.role.name,
                'status': obj.role.status
            }
        return None  # Return None if the user has no role assigned
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    fullName = serializers.CharField(read_only=True)  # FullName is read-only, derived from first_name and last_name.

    class Meta:
        model = User
        fields = ['email','firstName', 'lastName', 'fullName', 'middleName','phoneNumber', 'profilePicture', 'PANEL_CLIENT_KEY', 'start_date', 'end_date', 'client_type','is_enable','Address_line1','Address_line2','City','State','Country','Zip_code','Permanent_address','Current_address' ]

    def update(self, instance, validated_data):
        # Update first_name and last_name
        instance.firstName = validated_data.get('firstName', instance.firstName)
        instance.lastName = validated_data.get('lastName', instance.lastName)
        
        # Update other fields
        instance.email = validated_data.get('email', instance.email)
        instance.phoneNumber = validated_data.get('phoneNumber', instance.phoneNumber)
        instance.profilePicture = validated_data.get('profilePicture', instance.profilePicture)
        instance.PANEL_CLIENT_KEY = validated_data.get('PANEL_CLIENT_KEY', instance.PANEL_CLIENT_KEY)
        instance.start_date = validated_data.get('start_date', instance.start_date)
        instance.end_date = validated_data.get('end_date', instance.end_date)
        instance.client_type = validated_data.get('client_type', instance.client_type)
        instance.is_enable=validated_data.get('is_enable',instance.is_enable)
        instance.middleName=validated_data.get('middleName',instance.middleName)
        instance.Address_line1=validated_data.get('Address_line1',instance.Address_line1)
        instance.Address_line2=validated_data.get('Address_line2',instance.Address_line2)
        instance.City = validated_data.get('City', instance.City)
        instance.State = validated_data.get('State', instance.State)
        instance.Zip_code = validated_data.get('Zip_code', instance.Zip_code)
        instance.Permanent_address = validated_data.get('Permanent_address', instance.Permanent_address)
        instance.Current_address = validated_data.get('Current_address', instance.Current_address)
    
        # Save the updated instance
        instance.save()
        
        return instance
class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer()  # This will serialize the Role object into id and name fields

    class Meta:
        model = User
        fields = ['id', 'email', 'firstName', 'lastName', 'middleName','phoneNumber','Address_line1','Address_line2','City','State','Country','Zip_code','Permanent_address','Current_address' ,'role']
class NewUserCreateSerializer(serializers.ModelSerializer):
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())  # Accepts role ID directly
    class Meta:
        model = User
        fields = ['id', 'email', 'firstName', 'lastName', 'middleName','phoneNumber','role',]

    def validate_phoneNumber(self, value):
        # Check if the phone number is in a valid format
        if not value.isdigit() or len(value) != 10:  # Example validation for a 10-digit number
            raise serializers.ValidationError("Phone number must be a 10-digit number.")
        return value

    def validate(self, data):
        phone_number = data.get('phoneNumber')
        email = data.get('email')

        # Determine if we are updating an existing user or creating a new one
        if self.instance is not None:
            # Update scenario: Exclude the current instance when checking for duplicates
            if User.objects.exclude(id=self.instance.id).filter(phoneNumber=phone_number).exists():
                raise serializers.ValidationError({'phoneNumber': 'A user with this phone number already exists.'})
            if User.objects.exclude(id=self.instance.id).filter(email=email).exists():
                raise serializers.ValidationError({'email': 'A user with this email already exists.'})
        else:
            # Create scenario: Check for duplicates including the new data
            if User.objects.filter(phoneNumber=phone_number).exists():
                raise serializers.ValidationError({'phoneNumber': 'A user with this phone number already exists.'})
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError({'email': 'A user with this email already exists.'})

        return data

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.firstName = validated_data.get('firstName', instance.firstName)
        instance.lastName = validated_data.get('lastName', instance.lastName)
        instance.phoneNumber = validated_data.get('phoneNumber', instance.phoneNumber)
        instance.role = validated_data.get('role', instance.role)
        instance.middleName = validated_data.get('middleName', instance.middleName)
        instance.save()
        return instance

class KYCSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    class Meta:
        model = KYC
        fields = [
            'id', 'user','user_name', 'id_proof', 'document_file_front', 'document_file_back', 'is_verified', 'status',
            'verified_by', 'created_at', 'updated_at', 'address_proof_id', 'address_prof_front', 'address_prof_back'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'is_verified', 'verified_by']  # Restrict updates on some fields
    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.firstName} {obj.user.lastName}"  # Get the full name of the user
        return "NO name available"
class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['permission','group']  
class RolePermissionSerializer(serializers.ModelSerializer):
    role = RoleSerializer()
    permissions = serializers.SerializerMethodField()  # Custom field to handle permissions

    class Meta:
        model = RolePermission
        fields = ['role', 'permissions']

    def get_permissions(self, obj):
        # Use a dictionary to group permissions by "group"
        permission_dict = {}
        for perm in obj.permissions.all():
            group = perm.group
            if group not in permission_dict:
                permission_dict[group] = {
                    "permission": [],
                    "group": group
                }
            permission_dict[group]["permission"].append(perm.permission)

        # Format the permissions list in the required structure
        formatted_permissions = [
            {
                "permission": ", ".join(permissions["permission"]),  # Merge permissions into one string
                "group": group
            }
            for group, permissions in permission_dict.items()
        ]
        return formatted_permissions
class OrderLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLog
        fields = ['signal_time', 'order_type', 'symbol', 'price', 'strategy', 'created_at','user','status','failure_reason']
class UserActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivityLog
        fields = ['id', 'user', 'last_login_time', 'ip_address', 'session_key']  # Adjust fields as necessary        