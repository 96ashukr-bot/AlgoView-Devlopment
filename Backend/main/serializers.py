from django.forms import ValidationError
import requests
from rest_framework import serializers
from main.tasks import send_client_acc_email_async, send_email_async, send_email_pass_async
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
from django.utils import timezone

company_profile = CompanyProfileDetails.objects.first()
support_email = company_profile.company_support_email if company_profile else "support@example.com"
company_website = company_profile.company_website if company_profile else "https://example.com"
logo_url = company_profile.company_logo if company_profile else "https://example.com/logo.png"
login_link = company_profile.login_link if company_profile else "https://www.admin.algoview.in/login"
help_center_link = company_profile.help_center_link if company_profile else "https://www.admin.algoview.in/login"  
contact_number = company_profile.company_phone_number if company_profile else None
company_name = company_profile.company_name if company_profile else "AlgoView"

smtp_details=CompanySmtpDetails.objects.first()
default_from_email=smtp_details.default_from_email if smtp_details else None
  
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
class UserRegistrationSerializer_old(serializers.ModelSerializer):
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
        role = Role.objects.get(name='Client')
        # Start an atomic transaction
        with transaction.atomic():
            # Create the user with the generated password
            user = User.objects.create_user(**validated_data, password=password, external_user='true',role=role,type_of_user='is_client')
            
            # Try to send the password to the user's email
            try:
                print("pass...",password)
                EmailService.send_password_email(user.email, password,user.firstName,login_link,support_email,help_center_link,company_website,contact_number)
            except Exception as e:
                # If email sending fails, delete the user and raise an exception
                user.delete()
                raise serializers.ValidationError(f"Error sending email: {str(e)}")
        
        return user
class UserRegistrationSerializer(serializers.ModelSerializer):
    phoneNumber = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="Phone number already exists.")]
    )

    class Meta:
        model = User
        fields = ['email', 'firstName', 'lastName', 'phoneNumber', 'profilePicture', 'role']
    
    def create(self, validated_data):
        password = get_random_string(length=8)
        role = Role.objects.get(name='Client')
        with transaction.atomic():
            user = User.objects.create_user(**validated_data, password=password, role=role,external_user='true',type_of_user='is_client',is_client=True)
            

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
                    contact_number,
                    company_name
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
            otp_instance = OTP.objects.filter(user=user, is_verified=False).order_by('-created_at').first()

        # If no OTP exists, create a new one
            if not otp_instance:
                otp_instance = OTP.objects.create(user=user, is_verified=False)

            otp_instance.generate_otp()

            # otp_instance, created = OTP.objects.get_or_create(user=user, is_verified=False)
            # otp_instance.generate_otp()
            
            # Use Celery to send OTP asynchronously
            send_email_async.delay(
                subject='Your OTP Code',
                message=f'Your OTP code is {otp_instance.otp_code}.',
                from_email=default_from_email,
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
            # otp_instance, created = OTP.objects.get_or_create(user=user, is_verified=False)
            # otp_instance.generate_otp()
            otp_instance = OTP.objects.filter(user=user, is_verified=False).order_by('-created_at').first()

            # If no OTP exists, create a new one
            if not otp_instance:
                otp_instance = OTP.objects.create(user=user, is_verified=False)

            otp_instance.generate_otp()

            # Use Celery to send OTP asynchronously
            send_email_async.delay(
                subject='Your OTP Code',
                message=f'Your OTP code is {otp_instance.otp_code}.',
                from_email=default_from_email,
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
        if not user.role and user.external_user == "true"or  user.type_of_user == 'is_client' or user.is_client == True or user.role.name.lower() == 'client' or user.role.name == 'Client':
                messages = []
                if user.client_expiry_status:
                    messages.append("Your license has expired. Please renew it to continue using the service.")
                if not user.client_status:
                    messages.append("Your account is inactive. Please contact the administrator for assistance.")
                if messages:
                    send_client_acc_email_async.delay(
                        subject="Account Status Notification regarding license or account activity",
                        messages=messages,
                        username=user.firstName,
                        useremail=user.email
                    )
                    raise serializers.ValidationError({
                        "success": "False",
                        "message": messages
                    })
                # otp_instance, created = OTP.objects.get_or_create(user=user, is_verified=False)
                # otp_instance.generate_otp()
                otp_instance = OTP.objects.filter(user=user, is_verified=False).order_by('-created_at').first()

                # If no OTP exists, create a new one
                if not otp_instance:
                    otp_instance = OTP.objects.create(user=user, is_verified=False)

                otp_instance.generate_otp()

                # Send OTP to user's email
                send_email_async.delay(user.firstName,otp_instance.otp_code,user.email )
                # EmailService.send_login_email_otp(user.email, otp_instance.otp_code, user.firstName)

                return {
                    'message': f"OTP sent to your email: {email}. Please verify.",
                    'success':"True",
                    'role': {
                        'role_id': user.role.id if user.role else None,
                        'role_name': user.role.name if user.role else None,
                        'role_status': user.role.status if user.role else None,
                    },
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
                    'type_of_user':user.type_of_user if user.type_of_user else None,
                    'message': message,
                    'success':"True",
                    'email': user.email,
                    'is_client':False,
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'role': {
                        'role_id': user.role.id if user.role else None,
                        'role_name': user.role.name if user.role else None,
                        'role_status': user.role.status if user.role else None,
                    },
                    'ekyc_status': ekyc_status
                }

class CustomLoginSerializer000000(serializers.Serializer):
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
    #     from_email = default_from_email
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
        fields = ['email', 'firstName', 'lastName', 'fullName','middleName', 'phoneNumber', 'profilePicture', 'PANEL_CLIENT_KEY', 
                  'start_date', 'end_date', 'client_type' ,
            # Permanent Address Fields
            'permanent_add_line_1', 'permanent_add_line_2', 'permanent_city', 
            'permanent_state', 'permanent_country', 'permanent_zip_code','is_address_same',
            # Current Address Fields
            'current_add_line_1', 'current_add_line_2', 'current_city', 
            'current_state', 'current_country', 'current_zip_code','role','start_date_client','end_date_client',]

    def get_role(self, obj):
        if obj.role:
            return {
                'id': obj.role.id,
                'name': obj.role.name,
                'status': obj.role.status
            }
        return None  # Return None if the user has no role assigned
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    fullName = serializers.CharField()  # FullName is read-only, derived from first_name and last_name.

    class Meta:
        model = User
        fields = ['email','firstName', 'lastName', 'fullName', 'middleName','phoneNumber', 'profilePicture', 'PANEL_CLIENT_KEY', 'start_date', 'end_date', 'client_type',
            # Permanent Address Fields
            'permanent_add_line_1', 'permanent_add_line_2', 'permanent_city', 
            'permanent_state', 'permanent_country', 'permanent_zip_code','is_address_same',
            # Current Address Fields
            'current_add_line_1', 'current_add_line_2', 'current_city', 
            'current_state', 'current_country', 'current_zip_code',]

    def update(self, instance, validated_data):
        # Handle fullName and split if provided
        full_name = validated_data.get('fullName')
        if full_name:
            # Split full name into parts
            name_parts = full_name.split()
            instance.firstName = name_parts[0]  # First name

            if len(name_parts) > 1:
                instance.lastName = name_parts[-1]  # Last name
            else:
                instance.lastName = ""

            if len(name_parts) > 2:
                instance.middleName = ' '.join(name_parts[1:-1])  # Middle name
            else:
                instance.middleName = ""
        else:
            # Construct fullName from first, middle, and last names if available
            instance.firstName = validated_data.get('firstName', instance.firstName)
            instance.middleName = validated_data.get('middleName', instance.middleName)
            instance.lastName = validated_data.get('lastName', instance.lastName)

            # Construct fullName using available name parts
            full_name_parts = [instance.firstName]
            if instance.middleName:
                full_name_parts.append(instance.middleName)
            if instance.lastName:
                full_name_parts.append(instance.lastName)
            instance.fullName = " ".join(full_name_parts)

        # Update other fields
        instance.email = validated_data.get('email', instance.email)
        instance.phoneNumber = validated_data.get('phoneNumber', instance.phoneNumber)
        instance.profilePicture = validated_data.get('profilePicture', instance.profilePicture)
        instance.PANEL_CLIENT_KEY = validated_data.get('PANEL_CLIENT_KEY', instance.PANEL_CLIENT_KEY)
        instance.start_date = validated_data.get('start_date', instance.start_date)
        instance.end_date = validated_data.get('end_date', instance.end_date)
        instance.client_type = validated_data.get('client_type', instance.client_type)
        # instance.is_enable = validated_data.get('is_enable', instance.is_enable)

        # Update address fields
        instance.current_add_line_1 = validated_data.get('current_add_line_1', instance.current_add_line_1)
        instance.current_add_line_2 = validated_data.get('current_add_line_2', instance.current_add_line_2)
        instance.current_city = validated_data.get('current_city', instance.current_city)
        instance.current_state = validated_data.get('current_state', instance.current_state)
        instance.current_country = validated_data.get('current_country', instance.current_country)
        instance.current_zip_code = validated_data.get('current_zip_code', instance.current_zip_code)

        # Update is_address_same field
        is_address_same = validated_data.get('is_address_same', instance.is_address_same)
        instance.is_address_same = is_address_same

        if is_address_same:
            # If addresses are the same, set permanent address to current address
            instance.permanent_add_line_1 = instance.current_add_line_1
            instance.permanent_add_line_2 = instance.current_add_line_2
            instance.permanent_city = instance.current_city
            instance.permanent_state = instance.current_state
            instance.permanent_country = instance.current_country
            instance.permanent_zip_code = instance.current_zip_code
        else:
            instance.permanent_add_line_1 = validated_data.get('permanent_add_line_1', instance.permanent_add_line_1)
            instance.permanent_add_line_2 = validated_data.get('permanent_add_line_2', instance.permanent_add_line_2)
            instance.permanent_city = validated_data.get('permanent_city', instance.permanent_city)
            instance.permanent_state = validated_data.get('permanent_state', instance.permanent_state)
            instance.permanent_country = validated_data.get('permanent_country', instance.permanent_country)
            instance.permanent_zip_code = validated_data.get('permanent_zip_code', instance.permanent_zip_code)

        # Save the updated instance
        instance.save()

        return instance

   
class CreatedBySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'firstName', 'lastName', 'email']  # Include fields you want to show for created_by

class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer()  # Serializes the Role object into id and name fields
    created_by = CreatedBySerializer()  # Serializes the created_by field with detailed information
    client_count = serializers.IntegerField(read_only=True) 
    clients = serializers.SerializerMethodField()  # To fetch the list of clients' names
  # List of clients assigned to the sub-admin

    class Meta:
        model = User
        fields = ['id', 'email', 'firstName', 'lastName', 'fullName','middleName','phoneNumber',   
            # Permanent Address Fields
            'permanent_add_line_1', 'permanent_add_line_2', 'permanent_city', 
            'permanent_state', 'permanent_country', 'permanent_zip_code',
            # Current Address Fields
            'current_add_line_1', 'current_add_line_2', 'current_city', 
            'current_state', 'current_country', 'current_zip_code','role','created_by','is_active',
            'assigned_client','client_count','clients']
    def get_clients(self, obj):
        # Get the clients assigned to the Sub-Admin
        # Here, 'assigned_users' is the related field in the User model representing clients
        clients = obj.assigned_users.all()  # Adjust this according to your actual relationship
        return [client.fullName for client in clients]    
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
                raise serializers.ValidationError({'phoneNumber': 'User with this phone number already exists.'})
            if User.objects.exclude(id=self.instance.id).filter(email=email).exists():
                raise serializers.ValidationError({'email': 'User with this email already exists.'})
        else:
            # Create scenario: Check for duplicates including the new data
            if User.objects.filter(phoneNumber=phone_number).exists():
                raise serializers.ValidationError({'phoneNumber': 'A user with this phone number already exists.'})
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError({'email': 'User with this email already exists.'})

        return data
    

    def update(self, instance, validated_data):
        print("update user.....")
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
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    class Meta:
        model = KYC
        fields = [
            'id', 'user','first_name', 'last_name', 'email', 'phone','user_name', 'id_proof', 'document_file_front', 'document_file_back', 'is_verified', 'status',
            'verified_by', 'created_at', 'updated_at', 'address_proof_id', 'address_prof_front', 'address_prof_back'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'is_verified', 'verified_by']  # Restrict updates on some fields
    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.firstName} {obj.user.lastName}"  # Get the full name of the user
        return "NO name available"
    def get_first_name(self, obj):
        return obj.user.firstName if obj.user else None

    def get_last_name(self, obj):
        return obj.user.lastName if obj.user else None

    def get_email(self, obj):
        return obj.user.email if obj.user else None

    def get_phone(self, obj):
        return obj.user.phoneNumber if obj.user else None
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
        model = SignalOrderLog
        fields = ['id','signal_time', 'order_type', 'symbol', 'json_data','price', 'strategy', 'created_at']#'user','status','failure_reason']
class UserActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivityLog
        fields = ['id', 'user', 'last_login_time', 'ip_address', 'session_key']  # Adjust fields as necessary        
        
class CitesSerializer(serializers.ModelSerializer):
    class Meta:
        model=cities
        fields=['id','name','state_id','state_code']        
        
class StatesSerializers(serializers.ModelSerializer):
    class Meta:
        model=State
        fields =['id','name','country_id','country_code','state_code']
    
class LicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = License
        fields = '__all__'

class SegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Segment
        fields = ['id', 'name', 'short_name','status']
        
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = categories
        fields = ['id', 'name', 'status']  # Add other fields if necessary
class ServiceSerializerss(serializers.ModelSerializer):  
    class Meta:
        model = Services
        fields = '__all__'

class ServiceSerializer(serializers.ModelSerializer):
    segment = serializers.PrimaryKeyRelatedField(queryset=Segment.objects.all())
    category = serializers.PrimaryKeyRelatedField(queryset=categories.objects.all())

    class Meta:
        model = Services
        fields = ['id', 'service_name', 'created_at', 'updated_at', 'status', 'segment', 'category']

    def to_representation(self, instance):
        """Customize the output of the serializer to include nested segment and category data."""
        representation = super().to_representation(instance)
        representation['segment'] = SegmentSerializer(instance.segment).data
        representation['category'] = CategorySerializer(instance.category).data
        return representation           
class GroupServiceSerializer(serializers.ModelSerializer):
    segment = SegmentSerializer()  
    class Meta:
        model = GroupService
        fields = ['id', 'group_name', 'json_data', 'segment']     
class CreateGroupServiceSerializer(serializers.ModelSerializer):
    segment = serializers.PrimaryKeyRelatedField(queryset=Segment.objects.all())

    class Meta:
        model = GroupService  
        fields = ['id', 'group_name', 'json_data', 'segment']
    # def validate_group_name(self, value):
    #     if GroupService.objects.filter(group_name=value).exists():
    #         raise serializers.ValidationError("This group name already exists.")
    #     return value    
class GroupServiceUpdateSerializer(serializers.ModelSerializer):
    segment = serializers.PrimaryKeyRelatedField(queryset=Segment.objects.all())
    class Meta:
        model = GroupService  
        fields = ['id', 'group_name', 'json_data', 'segment']        
class StrategySerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=categories.objects.all())
    segment = serializers.PrimaryKeyRelatedField(queryset=Segment.objects.all())  # Ensure you have a queryset for segment
    
    # category = CategorySerializer()
    # segment = SegmentSerializer()
    class Meta:
        model = Strategies
        fields =['id','name','Lots','segment','category','description','Indicator','Strategy_Tester','Strategy_Logo',
                 'monthly_amount','quarterly_amount','half_yearly_amount','yearly_amount','status']
class clientSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','firstName','Strategy']

class GetStrategySerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    segment = SegmentSerializer()
    clients=clientSerializer(many=True)
    class Meta:
        model = Strategies
        fields =  '__all__'
class GetStrategySerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    segment = SegmentSerializer()
    clients=clientSerializer(many=True)
    class Meta:
        model = Strategies
        fields =  '__all__'
        
class GetBrokerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Broker
        fields = '__all__'       
class GetClientSerializer11(serializers.ModelSerializer):
    Groupservices = GroupServiceSerializer()
    license = LicenseSerializer()
    role = RoleSerializer()
    Broker=GetBrokerSerializer()
    class Meta:
        model = User
        fields = ['id', 'email', 'firstName', 'lastName', 'role', 'role_id']

        # fields  = ['id', 'firstName', 'lastName','phoneNumber', 'role','external_user','Groupservices','Broker','license','to_month']              
class GetClientSerializer(serializers.ModelSerializer):
    Group_service = GroupServiceSerializer()  # Make sure to match field names
    license = LicenseSerializer()
    role = RoleSerializer()
    Broker = GetBrokerSerializer()  # Ensure GetBrokerSerializer is correctly defined

    class Meta:
        model = User
        fields = ['id', 'email', 'firstName', 'lastName', 'phoneNumber', 'fullName', 'role',
                  'is_active', 'PANEL_CLIENT_KEY', 'external_user','client_type',
                  'Group_service', 'Broker', 'license', 'to_month']
class NewClientCreateSerializer(serializers.ModelSerializer):
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())  # Accepts role ID directly
    class Meta:
        model = User
        fields = ['id', 'email', 'firstName', 'lastName', 'phoneNumber', 'fullName', 'role',
                  'is_active', 'PANEL_CLIENT_KEY', 'external_user',
                  'Group_service', 'Broker', 'license', 'to_month']

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
                raise serializers.ValidationError({'phoneNumber': 'User with this phone number already exists.'})
            if User.objects.exclude(id=self.instance.id).filter(email=email).exists():
                raise serializers.ValidationError({'email': 'User with this email already exists.'})
        else:
            # Create scenario: Check for duplicates including the new data
            if User.objects.filter(phoneNumber=phone_number).exists():
                raise serializers.ValidationError({'phoneNumber': 'User with this phone number already exists.'})
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError({'email': 'User with this email already exists.'})

        return data
    
class ClientCreateSerializer(serializers.ModelSerializer):
    assigned_client = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    Strategy = serializers.PrimaryKeyRelatedField(queryset=Strategies.objects.all(), many=True, required=False)
    fullName = serializers.CharField(required=True)
    # Group_service = GroupServiceSerializer()  # Make sure to match field names
    # license = LicenseSerializer()
    # Broker = GetBrokerSerializer() 
    class Meta:
        model = User
        fields = ['id','email', 'firstName', 'lastName', 'phoneNumber', 'fullName', 'middleName','client_key',
                  'Group_service', 'license', 'user_license_month','to_month', 'created_by', 'assigned_client',
                  'Strategy','client_status','givenservices_to_month','start_date_client','end_date_client','client_expiry_status']
    # Phone number validation
    def validate_phoneNumber(self, value):
        # Check if the phone number is in a valid format
        if not value.isdigit() or len(value) != 10:  # Example validation for a 10-digit number
            raise serializers.ValidationError("Phone number must be a 10-digit number.")
        return value
    
    # def validate(self, data):
    #     phone_number = data.get('phoneNumber')
    #     email = data.get('email')


    #     if self.instance is not None:
    #         if User.objects.exclude(id=self.instance.id).filter(phoneNumber=phone_number).exists():
    #             raise serializers.ValidationError({'phoneNumber': 'A user with this phone number already exists.'})
    #         if User.objects.exclude(id=self.instance.id).filter(email=email).exists():
    #             raise serializers.ValidationError({'email': 'A user with this email already exists.'})
    #     else:
    #         if User.objects.filter(phoneNumber=phone_number).exists():
    #             raise serializers.ValidationError({'phoneNumber': 'A user with this phone number already exists.'})
    #         if User.objects.filter(email=email).exists():
    #             raise serializers.ValidationError({'email': 'A user with this email already exists.'})

    #     return data
    def validate(self, data):
        full_name = data.get('fullName')
        phone_number = data.get('phoneNumber')
        email = data.get('email')  # Ensure you get email from the data

        if not full_name:
            raise serializers.ValidationError({'fullName': 'Full name is required.'})

         # Check for duplicate phone number
        if phone_number:
        # Check if the phone number already exists for another user (excluding the current instance if updating)
            if self.instance is None:  # For new users, just check if phone exists
                if User.objects.filter(phoneNumber=phone_number).exists():
                    raise serializers.ValidationError({'phoneNumber': 'User with this phone number already exists.'})
            else:  # For updates, exclude the current user from the check
                if User.objects.exclude(id=self.instance.id).filter(phoneNumber=phone_number).exists():
                    raise serializers.ValidationError({'phoneNumber': 'User with this phone number already exists.'})

            # Check for duplicate email
            if email:
                # Check if the email already exists for another user (excluding the current instance if updating)
                if self.instance is None:  # For new users, just check if email exists
                    if User.objects.filter(email=email).exists():
                        raise serializers.ValidationError({'email': 'User with this email already exists.'})
                else:  # For updates, exclude the current user from the check
                    if User.objects.exclude(id=self.instance.id).filter(email=email).exists():
                        raise serializers.ValidationError({'email': 'User with this email already exists.'})

            # Split the full name into parts
            name_parts = full_name.split()

            # Assign names based on the number of parts
            data['firstName'] = name_parts[0]
            data['fullName'] = full_name  # Save the original full name

            if len(name_parts) == 1:
                # If only one name part, save it as firstName and fullName only
                data['middleName'] = ""
                data['lastName'] = ""
            elif len(name_parts) == 2:
                # If two name parts, assign first and last name
                data['lastName'] = name_parts[1]
                data['middleName'] = ""
            else:
                # If more than two parts, assign first, middle, and last names
                data['middleName'] = ' '.join(name_parts[1:-1])  # Middle name (if any)
                data['lastName'] = name_parts[-1]

            return data

    # Overriding the create method to handle assigned_client and strategies
    def create(self, validated_data):
        assigned_client = validated_data.pop('assigned_client', None)
        strategies = validated_data.pop('Strategy', [])
        role=Role.objects.get(name='Client')
        # Create the client without assigned_client initially
        client = User.objects.create(**validated_data)
        client.type_of_user = 'is_client'
        client.role = role
        client.is_client = True
        client.set_password(get_random_string(length=12))  # Generate random password

        # If assigned_client was provided, assign it
        if assigned_client:
            client.assigned_client = assigned_client

        # Assign strategies to the client
        if strategies:
            client.Strategy.set(strategies)

        client.save()

        return client
class AssignedClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'fullName']

class ClientListSerializer(serializers.ModelSerializer):
    assigned_client = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    Strategy = StrategySerializer(many=True, read_only=True) 
    Group_service = GroupServiceSerializer()  # Make sure to match field names
    license = LicenseSerializer()
    Broker = GetBrokerSerializer() 
    class Meta:
        model = User
        fields = ['id','email', 'firstName', 'middleName','fullName', 'lastName', 'client_status','phoneNumber',
                  'client_key', 'start_date_client','end_date_client','Broker', 'Group_service','license', 'user_license_month','to_month', 'created_by', 'assigned_client',
                  'Strategy','client_status','givenservices_to_month','demate_acc_uid','start_date_client', 'end_date_client','is_enable',
                  'created_at','client_expiry_status']
# class ClientListdetailsSerializer(serializers.ModelSerializer):
#     assigned_client = AssignedClientSerializer(read_only=True)
#     Strategy = StrategySerializer(many=True, read_only=True) 
#     Group_service = GroupServiceSerializer()  # Make sure to match field names
#     license = LicenseSerializer()
#     Broker = GetBrokerSerializer() 
#     class Meta:
#         model = User
#         fields = ['id','email', 'firstName', 'middleName','fullName', 'lastName', 'client_status','phoneNumber',
#                   'client_key', 'start_date_client','end_date_client','Broker', 'Group_service','license', 'user_license_month','to_month', 'created_by', 'assigned_client',
#                   'Strategy','client_status','givenservices_to_month','demate_acc_uid','start_date_client', 'end_date_client','is_enable',
#                   ]
class ClientupdateListSerializer(serializers.ModelSerializer):
    assigned_client = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    # Strategy = StrategySerializer(many=True, read_only=True)
    # Broker = GetBrokerSerializer(read_only=True)  # For reading broker data
    # broker_id = serializers.PrimaryKeyRelatedField(source='Broker', queryset=Broker.objects.all(), write_only=True)  # For writing broker data as an ID
    fullName = serializers.CharField(required=True)
    class Meta:
        model = User
        fields = [
            'id', 'email', 'firstName', 'middleName','fullName', 'lastName', 'client_status', 'phoneNumber',# 'client_key','Broker','broker_id''demate_acc_uid',
            'start_date_client', 'end_date_client', 'Group_service', 'license', 'user_license_month',
            'to_month', 'created_by', 'assigned_client', 'Strategy', 'client_status', 'givenservices_to_month',
            'is_enable',
        ]
    
    def update(self, instance, validated_data):
        # Handle fullName and split it if provided
        full_name = validated_data.get('fullName')
        if full_name:
            # Split full name into parts
            name_parts = full_name.split()
            
            # Assign names based on the number of parts
            validated_data['firstName'] = name_parts[0]
            validated_data['fullName'] = full_name  # Save the original full name
            
            if len(name_parts) == 1:
                # If only one name part, set firstName and fullName only
                validated_data['middleName'] = ""
                validated_data['lastName'] = ""
            elif len(name_parts) == 2:
                # If two name parts, assign first and last names
                validated_data['lastName'] = name_parts[1]
                validated_data['middleName'] = ""
            else:
                # If more than two parts, assign first, middle, and last names
                validated_data['middleName'] = ' '.join(name_parts[1:-1])  # Middle name (if any)
                validated_data['lastName'] = name_parts[-1]

        # Call the superclass update method with the modified validated_data
        return super().update(instance, validated_data)

class StrategyAssignSerializer(serializers.ModelSerializer):
    clients = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)

    class Meta:
        model = Strategies
        fields = ['id', 'name', 'clients']

    def update(self, instance, validated_data):
        # Pop the clients data from the validated data
        clients = validated_data.pop('clients', None)
        
        # Update the strategy with the remaining validated data
        instance = super().update(instance, validated_data)
        
        # Update the many-to-many field (clients) if provided
        if clients is not None:
            instance.clients.set(clients)  # Set the new clients to the strategy

        instance.save()
        return instance

# Serializer for displaying segments and sub-segments
class SegmentTSerializer(serializers.ModelSerializer):
    sub_segments = serializers.SerializerMethodField()

    class Meta:
        model = Segment
        fields = ['id', 'name', 'short_name', 'sub_segments']

    def get_sub_segments(self, obj):
        return SegmentTSerializer(obj.sub_segments.filter(status=True), many=True).data

class SubSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubSegment
        fields = ['id', 'name', 'short_name', 'status']


# # API View for all segments and sub-segments
# class ClientSegmentListView(generics.ListAPIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         segments = Segment.objects.all()
#         serializer = SegmentSerializer(segments, many=True)
#         return Response({"segments": serializer.data})


class ClientTradeSettingSerializer(serializers.ModelSerializer):

    segment = serializers.PrimaryKeyRelatedField(queryset=Segment.objects.all())
    sub_segment = serializers.PrimaryKeyRelatedField(queryset=SubSegment.objects.all())
    expiry_date = serializers.DateTimeField(required=False, allow_null=True)


    class Meta:
        model = ClientTradeSetting
        fields = ['id', 'client', 'segment', 'sub_segment', 'symbol', 
                  'strategy', 'broker', 'product_type', 'buy_sell', 'quantity', 
                  'trade_limit', 'max_loss_for_day', 'min_loss_for_day', 
                  'max_profit_for_day', 'min_profit_for_day', 'expiry_date', 'is_tread_status']
from django.utils.timezone import localtime
class GetclientTradedataSettingSerializer(serializers.ModelSerializer):
    segment = SegmentSerializer()  # Use the SegmentSerializer to include all segment details
    sub_segment = SubSegmentSerializer() 
        # Override the representation of expiry_date
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # Convert expiry_date to "DDMMMYYYY" format if it exists
        # if instance.expiry_date:
        #     representation['expiry_date'] = instance.expiry_date.strftime('%d%b%Y')  # Format date
        #     representation['expiry_date'] = representation['expiry_date'][:2] + representation['expiry_date'][2:].capitalize()  # Capitalize the month correctly
        if instance.expiry_date:
            representation['expiry_date'] = localtime(instance.expiry_date).date()  # Convert to local time and show only the date part
        
        return representation
    class Meta:
        model = ClientTradeSetting
        fields = ['id', 'client', 'segment', 'sub_segment', 'symbol', 
                  'strategy', 'broker', 'product_type', 'buy_sell', 'quantity', 
                  'trade_limit', 'max_loss_for_day', 'min_loss_for_day', 
                  'max_profit_for_day', 'min_profit_for_day', 'expiry_date', 'is_tread_status']

class SegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Segment
        fields = '__all__'  # Include all fields of the Segment model


class SubSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubSegment
        fields = '__all__'  # Include all fields of the SubSegment model


class ClientSegementsSerializer(serializers.ModelSerializer):
    segment = SegmentSerializer()  # Use the SegmentSerializer to include all segment details
    sub_segment = SubSegmentSerializer()  # Use the SubSegmentSerializer for sub-segment details
    # client = UserSerializer()  # Include user details using the UserSerializer

    class Meta:
        model = ClientTradeSetting
        fields = [
            'id', 'client', 'segment', 'sub_segment','is_tread_status','symbol', 
            'strategy', 'broker', 'product_type', 'buy_sell', 'quantity', 
            'trade_limit', 'max_loss_for_day', 'min_loss_for_day', 
            'max_profit_for_day', 'min_profit_for_day', 'expiry_date', 'is_tread_status']

class TreadLogSerializer(serializers.ModelSerializer):
    class Meta:
        model=TradeLog
        fileds=['client','trade_setting','symbol','is_trade_status','trade_date']    


class UserclientSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'firstName', 'middleName', 'lastName', 'fullName', 'phoneNumber','assigned_client', 
            'is_enable', 'is_active', 'start_date_client','end_date_client','client_status'
        ]


class ClientBrokerDetailsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientBrokerdetails
        fields = '__all__'
class ClientBrokerDetailsSerializer(serializers.ModelSerializer):
    broker_name = GetBrokerSerializer(read_only=True) 
    class Meta:
        model = ClientBrokerdetails
        fields = '__all__'
        
class ClientTradeSegementSerializer(serializers.ModelSerializer):
    segment = serializers.StringRelatedField()  # To display the name of the segment
    sub_segment = SubSegmentSerializer()#serializers.StringRelatedField()  # To display the name of the sub-segment

    class Meta:
        model = ClientTradeSetting
        fields ='__all__'

class ClientListdetailsSerializer(serializers.ModelSerializer):
    assigned_client = AssignedClientSerializer(read_only=True)
    Strategy = StrategySerializer(many=True, read_only=True)
    Group_service = GroupServiceSerializer()
    license = LicenseSerializer()
    Broker = GetBrokerSerializer()
    client_trade_settings = ClientTradeSegementSerializer(many=True, read_only=True, source='clienttradesetting_set')

    broker_names = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'firstName', 'middleName', 'fullName', 'lastName', 'client_status', 'phoneNumber',
            'client_key', 'start_date_client', 'end_date_client', 'Broker', 'Group_service', 'license',
            'user_license_month', 'to_month', 'created_by', 'assigned_client', 'Strategy', 'client_status',
            'givenservices_to_month', 'demate_acc_uid', 'start_date_client', 'end_date_client', 'is_enable',
            'client_trade_settings', 'broker_names','created_at','client_expiry_status'
        ]

    def get_broker_names(self, obj):
        # Filter ClientBrokerdetails for the current user
        brokers = ClientBrokerdetails.objects.filter(client=obj)
        # Return a list of broker names
        return [broker.broker_name.broker_name for broker in brokers if broker.broker_name]

class TradeorderhistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Tradeorderhistory
        fields = ['id', 'client', 'date', 'trading_symbol', 'Index_Symbol', 'order_id', 'order_status'
                , 'failure_reason', 'broker', 'order_params', 'strategy', 'Entry_type', 'Entry_Price', 
                'Exit_Price','Exit_type','EntryQty','ExitQty','trade_order_status', 'SignalEntry_time', 'SignalExit_time', 'Exchange', 'Segment','webhook_signal']


from rest_framework.exceptions import AuthenticationFailed
class ClientdashboardSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get("email")

        # Check if the email exists in the database
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed("Invalid email or user does not exist.")

        # Check if the user is active
        if not user.is_active:
            raise AuthenticationFailed("User account is disabled.")

        # Generate tokens for the user
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
        
class TradeOrderHistoryFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tradeorderhistory
        fields = ['id', 'client', 'date', 'trading_symbol', 'Index_Symbol', 'order_id',
                'broker', 'order_status', 'strategy', 'Entry_type', 'Entry_Price', 
                'Exit_Price','Exit_type','EntryQty','ExitQty','trade_order_status',
                'SignalEntry_time', 'SignalExit_time', 'Exchange', 'Segment','webhook_signal']
        
import re
class CompanyProfileDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfileDetails
        fields = '__all__'  # Includes all model fields
class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfileDetails
        fields = '__all__'  # Includes all model fields

    def validate_company_email(self, value):
        """Ensure email format is valid."""
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, value):
            raise serializers.ValidationError("Invalid email format.")
        return value

    def validate_company_support_email(self, value):
        """Ensure support email format is valid."""
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if value and not re.match(email_regex, value):
            raise serializers.ValidationError("Invalid support email format.")
        return value

    def validate_company_phone_number(self, value):
        """Ensure phone number is exactly 10 digits and numeric."""
        if value is None:
            return value  # Allow null values
        
        value_str = str(value)
        if not value_str.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits.")
        if len(value_str) != 10:
            raise serializers.ValidationError("Phone number must be exactly 10 digits.")
        return value


class CompanySmtpDetailsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CompanySmtpDetails
        fields = '__all__'

    def validate_email_host_user(self, value):
        """Ensure email_host_user is unique."""
        if CompanySmtpDetails.objects.filter(email_host_user=value).exists():
            raise serializers.ValidationError("Email host user already exists.")
        return value
    
    def validate_default_from_email(self, value):
        """Ensure default_from_email is unique."""
        if CompanySmtpDetails.objects.filter(default_from_email=value).exists():
            raise serializers.ValidationError("Default from email already exists.")
        return value
class CompanySmtpSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CompanySmtpDetails
        fields = '__all__'

class AdminLicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminLicense
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
