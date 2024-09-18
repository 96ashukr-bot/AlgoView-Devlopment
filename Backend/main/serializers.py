from django.forms import ValidationError
from rest_framework import serializers

from main.tasks import send_email_async
from .models import *
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from rest_framework.validators import UniqueValidator
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name']

class UserAssignRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'role']

    def update(self, instance, validated_data):
        instance.role = validated_data.get('role', instance.role)
        instance.save()
        return instance

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
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'firstName', 'lastName', 'phoneNumber', 'profilePicture', 'role', 'is_active', 'is_staff']

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.firstName = validated_data.get('firstName', instance.firstName)
        instance.lastName = validated_data.get('lastName', instance.lastName)
        instance.phoneNumber = validated_data.get('phoneNumber', instance.phoneNumber)
        instance.profilePicture = validated_data.get('profilePicture', instance.profilePicture)
        instance.role = validated_data.get('role', instance.role)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.is_staff = validated_data.get('is_staff', instance.is_staff)
        instance.save()
        return instance
        
class UserRegistrationSerializer_sync(serializers.ModelSerializer):
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
            user = User.objects.create_user(**validated_data, password=password)
            
            # Try to send the password to the user's email
            try:
                print("pass...",password)
                self.send_password_email(user.email, password)
            except Exception as e:
                # If email sending fails, delete the user and raise an exception
                user.delete()
                raise serializers.ValidationError(f"Error sending email: {str(e)}")
        
        return user

    def send_password_email(self, email, password):
        subject = 'Your account has been created'
        message = f'Your account has been created. Your password is: {password}'
        from_email = settings.DEFAULT_FROM_EMAIL
        send_mail(subject, message, from_email, [email])


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
        with transaction.atomic():
            user = User.objects.create_user(**validated_data, password=password)

            try:
                print("pass...",password)
                # Call the async task to send the email
                send_email_async.delay(
                    subject='Your account has been created',
                    message=f'Your account has been created. Your password is: {password}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email]
                )
            except Exception as e:
                user.delete()
                raise serializers.ValidationError(f"Error sending email: {str(e)}")
        
        return user

class CustomLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        print("kk")
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
class CustomLoginSerializer_sync(serializers.Serializer):
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
            self.send_email_otp(user.email, otp_instance.otp_code)

            return {
                'message': f"OTP sent to your email : {email}. Please verify "
            }
        else:
            if not user.is_new_password:
                return {
                    'message': 'Please change your password as this is a one-time temporary password.'
                }
            else:
                if user.is_new_password:
                    otp_instance, created = OTP.objects.get_or_create(user=user, is_verified=False)
                    otp_instance.generate_otp()
                    self.send_email_otp(user.email, otp_instance.otp_code)
                    return {
                        'message': f"OTP sent to your email: {email}. Please verify."
                    }

    def send_email_otp(self, email, otp_code):
        subject = 'Your OTP Code'
        message = f'Your OTP code is {otp_code}.'
        from_email = settings.DEFAULT_FROM_EMAIL
        send_mail(subject, message, from_email, [email])


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
        return user


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

        # Verify OTP
        otp_instance = OTP.objects.filter(user=user, is_verified=False).last()
        if otp_instance and otp_instance.otp_code == otp_code:
            otp_instance.is_verified = True
            otp_instance.save()
        else:
            raise serializers.ValidationError('Invalid OTP')

        # If OTP is verified, issue JWT tokens
        user.is_password_temporary = False
        user.save()
        refresh = RefreshToken.for_user(user)
        if not user.is_new_password:
            message= 'Please change your password as this is a one-time temporary password.'
        else:
            message="login successfully"
        return {
            'message':message,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            
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



class KYCSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYC
        fields = ['UserName', 'Date_Of_Birth', 'email', 'phone', 'document_type', 'document_file_front', 'document_file_back', 'is_verified']
        
    def validate(self, data):
        # Add any custom validation logic if needed
        return data