from django.forms import ValidationError
import requests
from rest_framework import serializers
import logging
from main.tasks import send_client_acc_email_async, send_email_async, send_email_pass_async, send_login_success_email
from main.utils import get_browser_info, get_client_ip, get_login_time
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
from datetime import date
from django.utils import timezone
from main.companysmtpsetails import get_company_profile,get_smtp_details
from main.broker_registry import (
    broker_field_is_configured,
    build_broker_setup_schema,
    get_broker_setup_spec,
    list_broker_schemas,
    normalize_broker_name,
)
from main.permissions import is_end_user
company_profile = get_company_profile()
smtp_details=get_smtp_details()
company_profile=company_profile if company_profile else None
smtp_details=smtp_details if smtp_details else None
# company_profile=None
support_email = company_profile.company_support_email if company_profile else "support@example.com"
company_website = company_profile.company_website if company_profile else "https://example.com"
logo_url = company_profile.company_logo if company_profile else "https://example.com/logo.png"
login_link = company_profile.login_link if company_profile else "https://www.admin.algoview.in/login"
help_center_link = company_profile.help_center_link if company_profile else "https://www.admin.algoview.in/login"  
contact_number = company_profile.company_phone_number if company_profile else None

# smtp_details=None
# smtp_details=CompanySmtpDetails.objects.first()
default_from_email=smtp_details.email_host_user if smtp_details else   "no-reply@example.com" 


def _resolve_role_by_aliases(*role_names):
    for role_name in role_names:
        role = Role.objects.filter(name__iexact=role_name).first()
        if role:
            return role
    canonical_role_name = next((name for name in role_names if name), None)
    if not canonical_role_name:
        raise serializers.ValidationError("Role resolution failed.")
    return Role.objects.create(name=canonical_role_name, status=Role.ACTIVE)


def _ensure_request_session_key(request):
    if not request or not hasattr(request, "session") or request.session is None:
        return None
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _create_fresh_otp(user):
    OTP.objects.filter(user=user, is_verified=False).update(is_verified=True)
    otp_instance = OTP.objects.create(user=user, is_verified=False)
    otp_instance.generate_otp()
    return otp_instance


def _safe_positive_int(value):
    try:
        parsed_value = int(value)
    except (TypeError, ValueError):
        return None
    return parsed_value if parsed_value > 0 else None


def _get_group_service_limits(group_service_name, sub_segment, client=None):
    if not sub_segment:
        return None

    candidate_group_services = []
    if client and getattr(client, "Group_service_id", None):
        client_group_service = client.Group_service
        if not group_service_name or client_group_service.group_name == group_service_name:
            candidate_group_services.append(client_group_service)

    if group_service_name:
        group_service = GroupService.objects.filter(group_name=group_service_name).first()
        if group_service and all(existing.id != group_service.id for existing in candidate_group_services):
            candidate_group_services.append(group_service)

    service_aliases = {sub_segment.name.casefold()}
    if getattr(sub_segment, "short_name", None):
        service_aliases.add(sub_segment.short_name.casefold())

    for group_service in candidate_group_services:
        json_data = group_service.json_data if isinstance(group_service.json_data, list) else []
        for entry in json_data:
            if not isinstance(entry, dict):
                continue

            service_name = str(entry.get("ScriptName") or entry.get("ServiceName") or "").strip()
            if service_name.casefold() not in service_aliases:
                continue

            return {
                "group_name": group_service.group_name,
                "service_name": service_name,
                "lot_size": _safe_positive_int(entry.get("LotSize")),
                "qty": _safe_positive_int(entry.get("Qty")),
                "product_type": str(entry.get("ProductType") or "").strip() or None,
            }

    return None


def _validate_multi_leg_legs(legs):
    if legs in (None, ""):
        return []
    if not isinstance(legs, list):
        raise serializers.ValidationError("Legs must be an array.")

    validated_legs = []
    for index, leg in enumerate(legs, start=1):
        if not isinstance(leg, dict):
            raise serializers.ValidationError(f"Leg {index} must be an object.")

        option_type = str(leg.get("option_type") or "").strip().upper()
        action = str(leg.get("action") or "").strip().upper()
        strike = leg.get("strike")
        ratio = leg.get("ratio") or 1

        if option_type not in {"CE", "PE"}:
            raise serializers.ValidationError(f"Leg {index} option type must be CE or PE.")
        if action not in {"BUY", "SELL"}:
            raise serializers.ValidationError(f"Leg {index} action must be BUY or SELL.")

        normalized_strike = _safe_positive_int(strike)
        normalized_ratio = _safe_positive_int(ratio)
        if normalized_strike is None:
            raise serializers.ValidationError(f"Leg {index} strike must be greater than 0.")
        if normalized_ratio is None:
            raise serializers.ValidationError(f"Leg {index} ratio must be greater than 0.")

        validated_legs.append({
            "option_type": option_type,
            "action": action,
            "strike": normalized_strike,
            "ratio": normalized_ratio,
        })

    return validated_legs


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
        fields = ['id', 'email', 'firstName','userName', 'lastName', 'phoneNumber', 'profilePicture', 'password']

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
        fields = ['email', 'firstName', 'lastName', 'userName','phoneNumber', 'profilePicture', 'role']


    def create(self, validated_data):
        # Generate a random password
        password = get_random_string(length=12)
        role = _resolve_role_by_aliases('Client', 'User')
        # Start an atomic transaction
        with transaction.atomic():
            # Create the user with the generated password
            user = User.objects.create_user(**validated_data, password=password, external_user='true',role=role,type_of_user='is_client')
            
            # Try to send the password to the user's email
            try:
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
        fields = ['email', 'firstName', 'lastName','userName', 'phoneNumber', 'profilePicture', 'role']
    
    def create(self, validated_data):
        password = get_random_string(length=8)
        role = _resolve_role_by_aliases('Client', 'User')
        with transaction.atomic():
            user = User.objects.create_user(**validated_data, password=password, role=role,external_user='true',type_of_user='is_client',is_client=True)
            

            try:
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
            otp_instance = _create_fresh_otp(user)

            # otp_instance, created = OTP.objects.get_or_create(user=user, is_verified=False)
            # otp_instance.generate_otp()
            
            EmailService.send_login_email_otp(user.email, otp_instance.otp_code, user.firstName)

            return {
                'message': f"OTP sent to your email: {email}. Please verify."
            }
        
        # Check if the user needs to change the temporary password
        if not user.is_new_password:
            return {
                'message': 'Please change your password as this is a one-time temporary password.'
            }
        else:
            otp_instance = _create_fresh_otp(user)

            EmailService.send_login_email_otp(user.email, otp_instance.otp_code, user.firstName)
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
        if is_end_user(user) or (not user.role and user.external_user == "true"):
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
                otp_instance = _create_fresh_otp(user)
                try:
                    EmailService.send_login_email_otp(user.email, otp_instance.otp_code, user.firstName)
                except Exception as exc:
                    raise serializers.ValidationError(
                        f"Unable to send OTP email. Please verify SMTP settings. {exc}"
                    )

                return {
                    'user_id': user.id,
                    'email': user.email,
                    'is_client': True,
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
                session_key = _ensure_request_session_key(request)
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
        otp_instance = OTP.objects.filter(user=user, is_verified=False).order_by('-expires_at', '-id').first()

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
            session_key = _ensure_request_session_key(request)

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
            browser = get_browser_info(request)
            ip_address = get_client_ip(request)
            login_time = get_login_time()
            message="login successfully"
            username=user.firstName
            email=user.email
            send_login_success_email.delay(username,email, browser, ip_address, login_time)

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
        fields = ['email', 'firstName', 'lastName', 'fullName','userName','middleName', 'phoneNumber', 'profilePicture', 'PANEL_CLIENT_KEY', 
                  'start_date', 'end_date', 'client_type' ,
            # Permanent Address Fields
            'permanent_add_line_1', 'permanent_add_line_2', 'permanent_city', 
            'permanent_state', 'permanent_country', 'permanent_zip_code','is_address_same',
            # Current Address Fields
            'current_add_line_1', 'current_add_line_2', 'current_city', 
            'current_state', 'current_country', 'current_zip_code','role','start_date_client','end_date_client',
            'created_at',
        ]

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
    user_id = serializers.IntegerField(source='id', read_only=True) 

    class Meta:
        model = User
        fields = ['user_id','email','firstName', 'lastName', 'userName','fullName', 'middleName','phoneNumber', 'profilePicture', 'PANEL_CLIENT_KEY', 'start_date', 'end_date', 'client_type',
            # Permanent Address Fields
            'permanent_add_line_1', 'permanent_add_line_2', 'permanent_city', 
            'permanent_state', 'permanent_country', 'permanent_zip_code','is_address_same',
            # Current Address Fields
            'current_add_line_1', 'current_add_line_2', 'current_city', 
            'current_state', 'current_country', 'current_zip_code',]

    def update(self, instance, validated_data):
        # Handle fullName and split if provided
        full_name = validated_data.get('fullName')
        userName=validated_data.get('userName')
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
        instance.userName=validated_data.get('userName',instance.userName)
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
        fields = ['id', 'email', 'firstName', 'lastName', 'userName','fullName','middleName','phoneNumber',   
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
        extra_kwargs = {
            'email': {'required': False, 'allow_null': True, 'allow_blank': True},
            'firstName': {'required': False, 'allow_null': True, 'allow_blank': True},
            'lastName': {'required': False, 'allow_null': True, 'allow_blank': True},
            'middleName': {'required': False, 'allow_null': True, 'allow_blank': True},
            'phoneNumber': {'required': False, 'allow_null': True, 'allow_blank': True},
        }

    def validate_phoneNumber(self, value):
        # Check if the phone number is in a valid format
        if value in (None, ""):
            return value
        if not value.isdigit() or len(value) != 10:  # Example validation for a 10-digit number
            raise serializers.ValidationError("Phone number must be a 10-digit number.")
        return value

    def validate(self, data):
        phone_number = data.get('phoneNumber')
        email = data.get('email')

        # Determine if we are updating an existing user or creating a new one
        if self.instance is not None:
            # Update scenario: Exclude the current instance when checking for duplicates
            if phone_number and User.objects.exclude(id=self.instance.id).filter(phoneNumber=phone_number).exists():
                raise serializers.ValidationError({'phoneNumber': 'User with this phone number already exists.'})
            if email and User.objects.exclude(id=self.instance.id).filter(email=email).exists():
                raise serializers.ValidationError({'email': 'User with this email already exists.'})
        else:
            # Create scenario: Check for duplicates including the new data
            if phone_number and User.objects.filter(phoneNumber=phone_number).exists():
                raise serializers.ValidationError({'phoneNumber': 'A user with this phone number already exists.'})
            if email and User.objects.filter(email=email).exists():
                raise serializers.ValidationError({'email': 'User with this email already exists.'})

        return data
    

    def update(self, instance, validated_data):
        logger.info("User profile update requested")
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
    def get_user_namesss(self, obj):
        if obj.user:
            return f"{obj.user.fName} {obj.user.lastName}"  # Get the full name of the user
        return "NO name available"
    def get_first_name(self, obj):
        return obj.user.firstName if obj.user else None

    def get_last_name(self, obj):
        return obj.user.lastName if obj.user else None

    def get_email(self, obj):
        return obj.user.email if obj.user else None

    def get_phone(self, obj):
        return obj.user.phoneNumber if obj.user else None
        # ✅ New method to fetch userName
    def get_user_name(self, obj):
        return obj.user.fullName if obj.user and obj.user.fullName else None
    
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
    category = serializers.PrimaryKeyRelatedField(queryset=categories.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Services
        fields = ['id', 'service_name', 'created_at', 'updated_at', 'status', 'segment', 'category']

    def to_representation(self, instance):
        """Customize the output of the serializer to include nested segment and category data."""
        representation = super().to_representation(instance)
        representation['segment'] = SegmentSerializer(instance.segment).data if instance.segment else None
        representation['category'] = CategorySerializer(instance.category).data if instance.category else None
        return representation           
class StrategydataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Strategies
        fields = '__all__'
class GroupServiceSerializer(serializers.ModelSerializer):
    segment = SegmentSerializer() 
    Strategy = StrategydataSerializer(many=True)
    class Meta:
        model = GroupService
        fields = ['id', 'group_name', 'json_data', 'segment','Strategy']     
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
        fields = ['id', 'group_name', 'json_data', 'segment','Strategy']        
class StrategySerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=categories.objects.all(), required=False, allow_null=True)
    segment = serializers.PrimaryKeyRelatedField(queryset=Segment.objects.all())  # Ensure you have a queryset for segment
    
    # category = CategorySerializer()
    # segment = SegmentSerializer()
    class Meta:
        model = Strategies
        fields =['id','name','Lots','segment','category','description','Indicator','Strategy_Tester','Strategy_Logo',
                 'monthly_amount','quarterly_amount','half_yearly_amount','yearly_amount','status',
                 'execution_mode', 'multi_leg_template']

    def validate(self, attrs):
        execution_mode = attrs.get("execution_mode", getattr(self.instance, "execution_mode", Strategies.EXECUTION_MODE_INDICATOR))
        multi_leg_template = attrs.get("multi_leg_template", getattr(self.instance, "multi_leg_template", None))

        if execution_mode == Strategies.EXECUTION_MODE_MULTI_LEG and not multi_leg_template:
            raise serializers.ValidationError({
                "multi_leg_template": "Multi-leg template is required for multi-leg option strategies."
            })

        if execution_mode != Strategies.EXECUTION_MODE_MULTI_LEG:
            attrs["multi_leg_template"] = None

        return attrs
class clientSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','firstName','Strategy']

class GetStrategySerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    segment = SegmentSerializer()
    clients=clientSerializer(many=True)
    execution_mode_label = serializers.CharField(source='get_execution_mode_display', read_only=True)
    multi_leg_template_label = serializers.SerializerMethodField()
    class Meta:
        model = Strategies
        fields =  '__all__'

    def get_multi_leg_template_label(self, obj):
        return obj.get_multi_leg_template_display() if obj.multi_leg_template else None

        
class GetBrokerSerializer(serializers.ModelSerializer):
    setup_schema = serializers.SerializerMethodField()

    class Meta:
        model = Broker
        fields = ['id', 'broker_name', 'is_active', 'description', 'created_at', 'updated_at', 'setup_schema']

    def get_setup_schema(self, obj):
        return build_broker_setup_schema(obj.broker_name)
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
        extra_kwargs = {
            'email': {'required': False, 'allow_null': True, 'allow_blank': True},
            'firstName': {'required': False, 'allow_null': True, 'allow_blank': True},
            'lastName': {'required': False, 'allow_null': True, 'allow_blank': True},
            'phoneNumber': {'required': False, 'allow_null': True, 'allow_blank': True},
            'fullName': {'required': False, 'allow_null': True, 'allow_blank': True},
            'PANEL_CLIENT_KEY': {'required': False, 'allow_null': True, 'allow_blank': True},
            'external_user': {'required': False, 'allow_null': True, 'allow_blank': True},
            'Group_service': {'required': False, 'allow_null': True},
            'Broker': {'required': False, 'allow_null': True},
            'license': {'required': False, 'allow_null': True},
            'to_month': {'required': False, 'allow_null': True},
        }

    def validate_phoneNumber(self, value):
        # Check if the phone number is in a valid format
        if value in (None, ""):
            return value
        if not value.isdigit() or len(value) != 10:  # Example validation for a 10-digit number
            raise serializers.ValidationError("Phone number must be a 10-digit number.")
        return value

    def validate(self, data):
        phone_number = data.get('phoneNumber')
        email = data.get('email')

        # Determine if we are updating an existing user or creating a new one
        if self.instance is not None:
            # Update scenario: Exclude the current instance when checking for duplicates
            if phone_number and User.objects.exclude(id=self.instance.id).filter(phoneNumber=phone_number).exists():
                raise serializers.ValidationError({'phoneNumber': 'User with this phone number already exists.'})
            if email and User.objects.exclude(id=self.instance.id).filter(email=email).exists():
                raise serializers.ValidationError({'email': 'User with this email already exists.'})
        else:
            # Create scenario: Check for duplicates including the new data
            if phone_number and User.objects.filter(phoneNumber=phone_number).exists():
                raise serializers.ValidationError({'phoneNumber': 'User with this phone number already exists.'})
            if email and User.objects.filter(email=email).exists():
                raise serializers.ValidationError({'email': 'User with this email already exists.'})

        return data
    
class ClientCreateSerializer(serializers.ModelSerializer):
    assigned_client = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    Strategy = serializers.PrimaryKeyRelatedField(queryset=Strategies.objects.all(), many=True, required=False)
    fullName = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    # Group_service = GroupServiceSerializer()  # Make sure to match field names
    # license = LicenseSerializer()
    # Broker = GetBrokerSerializer() 
    class Meta:
        model = User
        fields = ['id','email', 'firstName', 'lastName', 'userName','phoneNumber', 'fullName', 'middleName','client_key',
                  'Group_service', 'license', 'user_license_month','to_month', 'created_by', 'assigned_client',
                  'Strategy','client_status','givenservices_to_month','start_date_client','end_date_client','client_expiry_status']
        extra_kwargs = {
            'email': {'required': False, 'allow_null': True, 'allow_blank': True},
            'firstName': {'required': False, 'allow_null': True, 'allow_blank': True},
            'lastName': {'required': False, 'allow_null': True, 'allow_blank': True},
            'userName': {'required': False, 'allow_null': True, 'allow_blank': True},
            'phoneNumber': {'required': False, 'allow_null': True, 'allow_blank': True},
            'middleName': {'required': False, 'allow_null': True, 'allow_blank': True},
            'client_key': {'required': False, 'allow_null': True, 'allow_blank': True},
            'Group_service': {'required': False, 'allow_null': True},
            'license': {'required': False, 'allow_null': True},
            'user_license_month': {'required': False, 'allow_null': True},
            'to_month': {'required': False, 'allow_null': True},
            'created_by': {'required': False, 'allow_null': True},
            'givenservices_to_month': {'required': False, 'allow_null': True, 'allow_blank': True},
            'start_date_client': {'required': False, 'allow_null': True},
            'end_date_client': {'required': False, 'allow_null': True},
            'client_expiry_status': {'required': False},
        }
    # Phone number validation
    def validate_phoneNumber(self, value):
        # Check if the phone number is in a valid format
        if value in (None, ""):
            return value
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
        userName=data.get('userName')
        license_obj = data.get('license')
        license_name = (getattr(license_obj, 'name', '') or '').strip().lower()

        if not full_name:
            full_name = " ".join(
                part for part in [
                    data.get('firstName'),
                    data.get('middleName'),
                    data.get('lastName'),
                ] if part
            ).strip() or userName or email or phone_number or "Client"
            data['fullName'] = full_name

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
            data['userName']=userName
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

        if license_name == 'live':
            try:
                months = int(data.get('to_month') or 0)
            except (TypeError, ValueError):
                months = 0
            if not 1 <= months <= 12:
                raise serializers.ValidationError({'to_month': 'Live license duration must be between 1 and 12 months.'})
            data['to_month'] = months
            data['start_date_client'] = None
            data['end_date_client'] = None
        elif license_name == 'demo':
            data['to_month'] = None
            data['start_date_client'] = None
            data['end_date_client'] = None

        return data

    # Overriding the create method to handle assigned_client and strategies
    def create(self, validated_data):
        assigned_client = validated_data.pop('assigned_client', None)
        strategies = validated_data.pop('Strategy', [])
        role = _resolve_role_by_aliases('Client', 'User')
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
    client_expiry_status = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id','client_type', 'email', 'firstName', 'userName','middleName','fullName','phoneNumber' ,'lastName', 'client_status','phoneNumber',
                  'client_key', 'start_date_client','end_date_client','Broker', 'Group_service','license', 'user_license_month','to_month', 'created_by', 'assigned_client',
                  'Strategy','client_status','givenservices_to_month','demate_acc_uid','start_date_client', 'end_date_client','is_enable',
                  'created_at','client_expiry_status']

    def get_client_expiry_status(self, obj):
        if obj.end_date_client and obj.end_date_client < date.today():
            return False
        return True
        
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
            'id', 'email', 'firstName', 'middleName','userName','fullName', 'lastName', 'client_status', 'phoneNumber',# 'client_key','Broker','broker_id''demate_acc_uid',
            'start_date_client', 'end_date_client', 'Group_service', 'license', 'user_license_month',
            'to_month', 'created_by', 'assigned_client', 'Strategy', 'client_status', 'givenservices_to_month',
            'is_enable',
        ]

    def validate(self, data):
        license_obj = data.get('license') or getattr(self.instance, 'license', None)
        license_name = (getattr(license_obj, 'name', '') or '').strip().lower()
        to_month = data.get('to_month', getattr(self.instance, 'to_month', None))

        if license_name == 'live':
            try:
                months = int(to_month or 0)
            except (TypeError, ValueError):
                months = 0
            if not 1 <= months <= 12:
                raise serializers.ValidationError({'to_month': 'Live license duration must be between 1 and 12 months.'})
            data['to_month'] = months
            data['start_date_client'] = None
            data['end_date_client'] = None
        elif license_name == 'demo':
            data['to_month'] = None
            data['start_date_client'] = None
            data['end_date_client'] = None

        return data
    
    def update(self, instance, validated_data):
        # Handle fullName and split it if provided
        full_name = validated_data.get('fullName')
        userName=validated_data.get('userName')
        if full_name:
            # Split full name into parts
            name_parts = full_name.split()
            
            # Assign names based on the number of parts
            validated_data['firstName'] = name_parts[0]
            validated_data['fullName'] = full_name  # Save the original full name
            validated_data['userName']=userName
            
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
    order_type = serializers.ChoiceField(choices=["MARKET", "LIMIT"], required=False)
    buffer_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)


    class Meta:
        model = ClientTradeSetting
        fields = '__all__'
        # ['id', 'client', 'segment', 'sub_segment', 'symbol', 'group_service'
        #           'strategy', 'broker', 'product_type', 'buy_sell', 'quantity', 
        #           'trade_limit', 'max_loss_for_day', 'min_loss_for_day', 
        #           'max_profit_for_day', 'min_profit_for_day', 'expiry_date', 'is_tread_status','sl_type','stop_loss','target']
    def validate(self, attrs):
        client = attrs.get("client", getattr(self.instance, "client", None))
        sub_segment = attrs.get("sub_segment", getattr(self.instance, "sub_segment", None))

        if sub_segment:
            attrs["segment"] = attrs.get("segment", getattr(self.instance, "segment", None)) or sub_segment.segment
            if not str(attrs.get("symbol", getattr(self.instance, "symbol", "")) or "").strip():
                attrs["symbol"] = str(sub_segment.short_name or sub_segment.name or "").strip() or None

        if client:
            if not str(attrs.get("group_service", getattr(self.instance, "group_service", "")) or "").strip():
                attrs["group_service"] = getattr(getattr(client, "Group_service", None), "group_name", None)

            if not str(attrs.get("broker", getattr(self.instance, "broker", "")) or "").strip():
                broker_detail = ClientBrokerdetails.objects.filter(client=client).select_related("broker_name").first()
                if broker_detail and broker_detail.broker_name:
                    attrs["broker"] = broker_detail.broker_name.broker_name

        order_type = str(attrs.get("order_type", getattr(self.instance, "order_type", "LIMIT")) or "LIMIT").upper()
        attrs["order_type"] = order_type

        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({
                "end_time": "End time must be after start time."
            })

        sl_type = attrs.get("sl_type", getattr(self.instance, "sl_type", None))
        if sl_type not in (None, ""):
            normalized_sl_type = str(sl_type).strip().upper()
            if normalized_sl_type in {"%", "PERCENT", "PERCENTAGE"}:
                attrs["sl_type"] = "PERCENTAGE"
            elif normalized_sl_type in {"POINT", "POINTS"}:
                attrs["sl_type"] = "POINTS"
            else:
                raise serializers.ValidationError({
                    "sl_type": "SL-TP type must be either Percentage or Points."
                })
        else:
            attrs["sl_type"] = None

        for numeric_field in ("stop_loss", "target"):
            raw_value = attrs.get(numeric_field, getattr(self.instance, numeric_field, None))
            if raw_value in (None, ""):
                attrs[numeric_field] = None
                continue

            normalized_value = _safe_positive_int(raw_value)
            if normalized_value is None:
                raise serializers.ValidationError({
                    numeric_field: f"{numeric_field.replace('_', ' ').title()} must be greater than 0."
                })
            attrs[numeric_field] = normalized_value

        buffer_percentage = attrs.get("buffer_percentage", getattr(self.instance, "buffer_percentage", None))
        if order_type == "LIMIT":
            if buffer_percentage is not None:
                buffer_value = float(buffer_percentage)
                if buffer_value < 0.1 or buffer_value > 10.0:
                    raise serializers.ValidationError({
                        "buffer_percentage": "Buffer percentage must be between 0.1 and 10.0."
                    })
        else:
            attrs["buffer_percentage"] = None

        quantity = attrs.get("quantity", getattr(self.instance, "quantity", None))
        if quantity is not None:
            quantity = _safe_positive_int(quantity)
            if quantity is None:
                raise serializers.ValidationError({
                    "quantity": "Quantity must be greater than 0."
                })

            group_service_name = attrs.get("group_service", getattr(self.instance, "group_service", None))
            group_service_limits = _get_group_service_limits(group_service_name, sub_segment, client)

            if group_service_limits and not str(attrs.get("product_type", getattr(self.instance, "product_type", "")) or "").strip():
                attrs["product_type"] = group_service_limits.get("product_type")

            if group_service_limits:
                max_qty = group_service_limits.get("qty")
                lot_size = group_service_limits.get("lot_size")

                if max_qty and quantity > max_qty:
                    raise serializers.ValidationError({
                        "quantity": (
                            f"Quantity cannot exceed {max_qty} for "
                            f"{group_service_limits['service_name']} in group service "
                            f"{group_service_limits['group_name']}."
                        )
                    })

                if not max_qty and lot_size and quantity > lot_size:
                    raise serializers.ValidationError({
                        "quantity": (
                            f"Quantity cannot exceed lot size {lot_size} for "
                            f"{group_service_limits['service_name']} in group service "
                            f"{group_service_limits['group_name']}."
                        )
                    })
        return attrs


class ClientMultiLegStrategySettingSerializer(serializers.ModelSerializer):
    strategy = serializers.PrimaryKeyRelatedField(queryset=Strategies.objects.all())
    segment = serializers.PrimaryKeyRelatedField(queryset=Segment.objects.all(), required=False, allow_null=True)
    expiry_date = serializers.DateTimeField(required=False, allow_null=True)
    order_type = serializers.ChoiceField(choices=["MARKET", "LIMIT"], required=False)
    buffer_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model = ClientMultiLegStrategySetting
        fields = '__all__'

    def validate(self, attrs):
        client = attrs.get("client", getattr(self.instance, "client", None))
        strategy = attrs.get("strategy", getattr(self.instance, "strategy", None))

        if strategy and strategy.execution_mode != Strategies.EXECUTION_MODE_MULTI_LEG:
            raise serializers.ValidationError({
                "strategy": "Only multi-leg strategies can be configured here."
            })

        attrs["legs"] = _validate_multi_leg_legs(attrs.get("legs", getattr(self.instance, "legs", [])))

        if client:
            if not str(attrs.get("group_service", getattr(self.instance, "group_service", "")) or "").strip():
                attrs["group_service"] = getattr(getattr(client, "Group_service", None), "group_name", None)

            if not str(attrs.get("broker", getattr(self.instance, "broker", "")) or "").strip():
                broker_detail = ClientBrokerdetails.objects.filter(client=client).select_related("broker_name").first()
                if broker_detail and broker_detail.broker_name:
                    attrs["broker"] = broker_detail.broker_name.broker_name

        order_type = str(attrs.get("order_type", getattr(self.instance, "order_type", "LIMIT")) or "LIMIT").upper()
        attrs["order_type"] = order_type

        sl_type = attrs.get("sl_type", getattr(self.instance, "sl_type", None))
        if sl_type not in (None, ""):
            normalized_sl_type = str(sl_type).strip().upper()
            if normalized_sl_type in {"%", "PERCENT", "PERCENTAGE"}:
                attrs["sl_type"] = "PERCENTAGE"
            elif normalized_sl_type in {"POINT", "POINTS"}:
                attrs["sl_type"] = "POINTS"
            else:
                raise serializers.ValidationError({
                    "sl_type": "SL-TP type must be either Percentage or Points."
                })
        else:
            attrs["sl_type"] = None

        for numeric_field in ("stop_loss", "target", "quantity", "trade_limit"):
            raw_value = attrs.get(numeric_field, getattr(self.instance, numeric_field, None))
            if raw_value in (None, ""):
                attrs[numeric_field] = None
                continue

            normalized_value = _safe_positive_int(raw_value)
            if normalized_value is None:
                raise serializers.ValidationError({
                    numeric_field: f"{numeric_field.replace('_', ' ').title()} must be greater than 0."
                })
            attrs[numeric_field] = normalized_value

        buffer_percentage = attrs.get("buffer_percentage", getattr(self.instance, "buffer_percentage", None))
        if order_type == "LIMIT":
            if buffer_percentage is not None:
                buffer_value = float(buffer_percentage)
                if buffer_value < 0.1 or buffer_value > 10.0:
                    raise serializers.ValidationError({
                        "buffer_percentage": "Buffer percentage must be between 0.1 and 10.0."
                    })
        else:
            attrs["buffer_percentage"] = None

        return attrs

from django.utils.timezone import localtime
class GetclientTradedataSettingSerializer(serializers.ModelSerializer):
    segment = SegmentSerializer()  # Use the SegmentSerializer to include all segment details
    sub_segment = SubSegmentSerializer() 
    script_name = serializers.SerializerMethodField()
    group_lot_size = serializers.SerializerMethodField()
    group_qty_limit = serializers.SerializerMethodField()
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

    def get_script_name(self, obj):
        group_service_limits = _get_group_service_limits(obj.group_service, obj.sub_segment, obj.client)
        return group_service_limits.get("service_name") if group_service_limits else None

    def get_group_lot_size(self, obj):
        group_service_limits = _get_group_service_limits(obj.group_service, obj.sub_segment, obj.client)
        return group_service_limits.get("lot_size") if group_service_limits else None

    def get_group_qty_limit(self, obj):
        group_service_limits = _get_group_service_limits(obj.group_service, obj.sub_segment, obj.client)
        return group_service_limits.get("qty") if group_service_limits else None

    class Meta:
        model = ClientTradeSetting
        fields = ['id', 'client', 'segment', 'sub_segment', 'symbol', 'group_service',
                  'script_name', 'group_lot_size', 'group_qty_limit',
                  'strategy', 'broker', 'product_type', 'order_type', 'buffer_percentage', 'buy_sell', 'quantity', 
                  'trade_limit', 'max_loss_for_day',
                  'max_profit_for_day', 'expiry_date', 'is_tread_status','sl_type','stop_loss','target']

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
    script_name = serializers.SerializerMethodField()
    group_lot_size = serializers.SerializerMethodField()
    group_qty_limit = serializers.SerializerMethodField()
    # client = UserSerializer()  # Include user details using the UserSerializer

    def get_script_name(self, obj):
        group_service_limits = _get_group_service_limits(obj.group_service, obj.sub_segment, obj.client)
        return group_service_limits.get("service_name") if group_service_limits else None

    def get_group_lot_size(self, obj):
        group_service_limits = _get_group_service_limits(obj.group_service, obj.sub_segment, obj.client)
        return group_service_limits.get("lot_size") if group_service_limits else None

    def get_group_qty_limit(self, obj):
        group_service_limits = _get_group_service_limits(obj.group_service, obj.sub_segment, obj.client)
        return group_service_limits.get("qty") if group_service_limits else None

    class Meta:
        model = ClientTradeSetting
        fields = [
            'id', 'client', 'segment', 'sub_segment','is_tread_status','symbol', 'group_service',
            'script_name', 'group_lot_size', 'group_qty_limit',
            'strategy', 'broker', 'product_type', 'order_type', 'buffer_percentage', 'buy_sell', 'quantity', 
            'trade_limit', 'max_loss_for_day',
            'max_profit_for_day', 'expiry_date', 'is_tread_status','sl_type','stop_loss','target']

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
    broker_API_KEY = serializers.CharField(required=False, allow_blank=True, write_only=True)
    broker_API_SKEY = serializers.CharField(required=False, allow_blank=True, write_only=True)
    broker_pass = serializers.CharField(required=False, allow_blank=True, write_only=True)
    broker_Totp_Authcode = serializers.CharField(required=False, allow_blank=True, write_only=True)
    access_token = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = ClientBrokerdetails
        fields = [
            'id',
            'client',
            'broker_name',
            'broker_API_KEY',
            'broker_API_SKEY',
            'broker_API_UID',
            'broker_Demate_User_Name',
            'broker_pass',
            'broker_Totp_Authcode',
            'access_token',
            'access_token_expiry',
            'isTokenExpired',
        ]
        read_only_fields = ['id', 'client', 'access_token_expiry', 'isTokenExpired']

    def validate(self, attrs):
        broker_obj = attrs.get("broker_name") or getattr(self.instance, "broker_name", None)
        if not broker_obj:
            return attrs

        submitted_keys = set(attrs.keys())
        if submitted_keys and submitted_keys <= {"broker_name"}:
            return attrs

        spec = get_broker_setup_spec(broker_obj.broker_name)
        if not spec:
            return attrs

        errors = {}
        for field_spec in spec["fields"]:
            key = field_spec["key"]
            if key in attrs:
                incoming_value = attrs.get(key)
                if isinstance(incoming_value, str):
                    incoming_value = incoming_value.strip()
                if field_spec.get("required") and not incoming_value and not broker_field_is_configured(self.instance, key):
                    errors.setdefault(key, []).append(f"{field_spec['label']} is required for {broker_obj.broker_name}.")
            elif field_spec.get("required") and not broker_field_is_configured(self.instance, key):
                errors.setdefault(key, []).append(f"{field_spec['label']} is required for {broker_obj.broker_name}.")

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def update(self, instance, validated_data):
        api_key = validated_data.pop('broker_API_KEY', None)
        api_secret = validated_data.pop('broker_API_SKEY', None)
        broker_pass = validated_data.pop('broker_pass', None)
        totp_secret = validated_data.pop('broker_Totp_Authcode', None)
        access_token = validated_data.pop('access_token', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if api_key is not None:
            instance.broker_API_KEY = api_key or None
        if api_secret is not None:
            if instance.is_angel_one_broker():
                instance.set_broker_api_secret(api_secret or None)
            else:
                instance.broker_API_SKEY = api_secret or None
        if broker_pass is not None:
            if instance.is_angel_one_broker():
                instance.set_broker_password(broker_pass or None)
            else:
                instance.broker_pass = broker_pass or None
        if totp_secret is not None:
            if instance.is_angel_one_broker():
                instance.set_broker_totp_secret(totp_secret or None)
            else:
                instance.broker_Totp_Authcode = totp_secret or None
        if access_token is not None:
            if instance.is_angel_one_broker():
                instance.set_session_tokens(access_token or None, instance.get_refresh_token_secure(), instance.get_feed_token_secure(), expiry=instance.access_token_expiry)
            else:
                instance.access_token = access_token or None

        if instance.is_angel_one_broker():
            instance.clear_legacy_angel_sensitive_fields()

        instance.save()
        return instance

    def create(self, validated_data):
        instance = ClientBrokerdetails(**{
            key: value for key, value in validated_data.items()
            if key not in {'broker_API_KEY', 'broker_API_SKEY', 'broker_pass', 'broker_Totp_Authcode', 'access_token'}
        })
        if 'broker_API_KEY' in validated_data:
            instance.broker_API_KEY = validated_data.get('broker_API_KEY') or None
        if 'broker_API_SKEY' in validated_data:
            if instance.is_angel_one_broker():
                instance.set_broker_api_secret(validated_data.get('broker_API_SKEY') or None)
            else:
                instance.broker_API_SKEY = validated_data.get('broker_API_SKEY') or None
        if 'broker_pass' in validated_data:
            if instance.is_angel_one_broker():
                instance.set_broker_password(validated_data.get('broker_pass') or None)
            else:
                instance.broker_pass = validated_data.get('broker_pass') or None
        if 'broker_Totp_Authcode' in validated_data:
            if instance.is_angel_one_broker():
                instance.set_broker_totp_secret(validated_data.get('broker_Totp_Authcode') or None)
            else:
                instance.broker_Totp_Authcode = validated_data.get('broker_Totp_Authcode') or None
        if 'access_token' in validated_data:
            if instance.is_angel_one_broker():
                instance.set_session_tokens(validated_data.get('access_token') or None, None, None)
            else:
                instance.access_token = validated_data.get('access_token') or None
        if instance.is_angel_one_broker():
            instance.clear_legacy_angel_sensitive_fields()
        instance.save()
        return instance


class ClientBrokerDetailsSerializer(serializers.ModelSerializer):
    broker_name = GetBrokerSerializer(read_only=True) 
    selected_broker_name = serializers.SerializerMethodField()
    selected_broker_slug = serializers.SerializerMethodField()
    broker_setup = serializers.SerializerMethodField()
    available_brokers = serializers.SerializerMethodField()
    has_api_key = serializers.SerializerMethodField()
    has_api_secret = serializers.SerializerMethodField()
    has_password = serializers.SerializerMethodField()
    has_totp_secret = serializers.SerializerMethodField()
    has_access_token = serializers.SerializerMethodField()
    has_refresh_token = serializers.SerializerMethodField()
    has_feed_token = serializers.SerializerMethodField()

    class Meta:
        model = ClientBrokerdetails
        fields = [
            'id',
            'client',
            'broker_name',
            'selected_broker_name',
            'selected_broker_slug',
            'broker_setup',
            'available_brokers',
            'broker_API_UID',
            'broker_Demate_User_Name',
            'access_token_expiry',
            'isTokenExpired',
            'tokenCreatedAt',
            'broker_last_logout_at',
            'has_api_key',
            'has_api_secret',
            'has_password',
            'has_totp_secret',
            'has_access_token',
            'has_refresh_token',
            'has_feed_token',
        ]

    def get_selected_broker_name(self, obj):
        if not obj or not obj.broker_name:
            return None
        setup = build_broker_setup_schema(obj.broker_name.broker_name, obj)
        return setup.get("display_name") if setup else obj.broker_name.broker_name

    def get_selected_broker_slug(self, obj):
        return normalize_broker_name(obj.broker_name.broker_name).replace(" ", "-") if obj and obj.broker_name else None

    def get_broker_setup(self, obj):
        if not obj or not obj.broker_name:
            return None
        return build_broker_setup_schema(obj.broker_name.broker_name, obj)

    def get_available_brokers(self, obj):
        brokers = self.context.get("available_brokers")
        if brokers is None:
            brokers = Broker.objects.filter(is_active=True).order_by("broker_name")
        return list_broker_schemas(brokers, obj)

    def get_has_api_key(self, obj):
        return bool(obj.broker_API_KEY)

    def get_has_api_secret(self, obj):
        if obj.is_angel_one_broker():
            return bool(obj.get_broker_api_secret() or obj.broker_API_SKEY)
        return bool(obj.broker_API_SKEY)

    def get_has_password(self, obj):
        if obj.is_angel_one_broker():
            return bool(obj.get_broker_password() or obj.broker_pass)
        return bool(obj.broker_pass)

    def get_has_totp_secret(self, obj):
        if obj.is_angel_one_broker():
            return bool(obj.get_broker_totp_secret() or obj.broker_Totp_Authcode)
        return bool(obj.broker_Totp_Authcode)

    def get_has_access_token(self, obj):
        if obj.is_angel_one_broker():
            return bool(obj.get_access_token_secure() or obj.access_token)
        return bool(obj.access_token)

    def get_has_refresh_token(self, obj):
        if obj.is_angel_one_broker():
            return bool(obj.get_refresh_token_secure() or obj.refreshToken)
        return bool(obj.refreshToken)

    def get_has_feed_token(self, obj):
        if obj.is_angel_one_broker():
            return bool(obj.get_feed_token_secure() or obj.feed_token)
        return bool(obj.feed_token)
        
class ClientTradeSegementSerializer(serializers.ModelSerializer):
    segment = serializers.StringRelatedField()  # To display the name of the segment
    sub_segment = SubSegmentSerializer()#serializers.StringRelatedField()  # To display the name of the sub-segment

    class Meta:
        model = ClientTradeSetting
        fields ='__all__'


class ClientMultiLegTradeSettingReadSerializer(serializers.ModelSerializer):
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    strategy_execution_mode = serializers.CharField(source='strategy.execution_mode', read_only=True)
    multi_leg_template = serializers.CharField(source='strategy.multi_leg_template', read_only=True)
    multi_leg_template_label = serializers.SerializerMethodField()
    segment = SegmentSerializer()

    class Meta:
        model = ClientMultiLegStrategySetting
        fields = [
            'id', 'client', 'strategy', 'strategy_name', 'strategy_execution_mode',
            'multi_leg_template', 'multi_leg_template_label', 'segment', 'underlying', 'group_service', 'broker',
            'product_type', 'order_type', 'buffer_percentage', 'quantity', 'trade_limit',
            'max_loss_for_day', 'max_profit_for_day', 'expiry_date', 'start_time', 'end_time', 'is_tread_status',
            'sl_type', 'stop_loss', 'target', 'legs', 'created_at', 'updated_at',
        ]

    def get_multi_leg_template_label(self, obj):
        return obj.strategy.get_multi_leg_template_display() if obj.strategy and obj.strategy.multi_leg_template else None

class ClientListdetailsSerializer(serializers.ModelSerializer):
    assigned_client = AssignedClientSerializer(read_only=True)
    Strategy = StrategySerializer(many=True, read_only=True)
    Group_service = GroupServiceSerializer()
    license = LicenseSerializer()
    Broker = GetBrokerSerializer()
    client_trade_settings = ClientTradeSegementSerializer(many=True, read_only=True, source='clienttradesetting_set')
    multi_leg_trade_settings = ClientMultiLegTradeSettingReadSerializer(many=True, read_only=True)

    broker_names = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'firstName','userName', 'middleName', 'fullName', 'lastName', 'client_status', 'phoneNumber',
            'client_key', 'start_date_client', 'end_date_client', 'Broker', 'Group_service', 'license',
            'user_license_month', 'to_month', 'created_by', 'assigned_client', 'Strategy', 'client_status',
            'givenservices_to_month', 'demate_acc_uid', 'start_date_client', 'end_date_client', 'is_enable',
            'client_trade_settings', 'multi_leg_trade_settings', 'broker_names','created_at','client_expiry_status'
        ]

    def get_broker_names(self, obj):
        # Filter ClientBrokerdetails for the current user
        brokers = ClientBrokerdetails.objects.filter(client=obj)
        # Return a list of broker names
        return [broker.broker_name.broker_name for broker in brokers if broker.broker_name]

class ClientnameSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User  # Your User model
        fields = ['id', 'firstName', 'middleName', 'lastName', 'email', 'full_name']

    def get_full_name(self, obj):
        names = [obj.firstName]
        if obj.middleName:
            names.append(obj.middleName)
        if obj.lastName:
            names.append(obj.lastName)
        return " ".join(names)

class TradeorderhistorySerializer(serializers.ModelSerializer):
    client = ClientnameSerializer(read_only=True)  # Use the nested serializer

    class Meta:
        model = Tradeorderhistory
        fields = ['id', 'client', 'date', 'trading_symbol','GroupService' ,'Index_Symbol', 'order_id', 'order_status','transaction_type'
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
        fields = ['id', 'client', 'date', 'trading_symbol', 'GroupService','Index_Symbol', 'order_id','transaction_type',
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

    def validate(self, attrs):
        email_host = str(attrs.get("email_host", getattr(self.instance, "email_host", "")) or "").strip()
        email_host_user = str(attrs.get("email_host_user", getattr(self.instance, "email_host_user", "")) or "").strip()
        default_from_email = str(attrs.get("default_from_email", getattr(self.instance, "default_from_email", "")) or "").strip()
        email_port = attrs.get("email_port", getattr(self.instance, "email_port", None))

        sender_email = (default_from_email or email_host_user).lower()
        if email_host.lower() == "smtp.zoho.com" and sender_email.endswith(".in"):
            attrs["email_host"] = "smtp.zoho.in"

        if str(email_host or attrs.get("email_host", "")).lower().startswith("smtp.zoho"):
            attrs["email_use_tls"] = int(email_port or 587) != 465

        return attrs

class AdminLicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminLicense
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class WebsocketDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebsocketDetails
        fields = ["id", "Auth_token", "token_status"]
        
class BrokerLogSerializer(serializers.ModelSerializer):
    last_login = serializers.DateTimeField(source='tokenCreatedAt', format="%Y-%m-%d %H:%M:%S", read_only=True)
    logout_time = serializers.DateTimeField(source='access_token_expiry', format="%Y-%m-%d %H:%M:%S", read_only=True)
    # client_id = serializers.CharField(source='client.id', read_only=True)  # adjust field name if needed
    broker = serializers.StringRelatedField(source='broker_name')

    class Meta:
        model = ClientBrokerdetails
        fields = ['id', 'broker', 'last_login', 'logout_time', 'isTokenExpired']
logger = logging.getLogger(__name__)
