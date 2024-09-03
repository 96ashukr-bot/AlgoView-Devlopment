from rest_framework import serializers
from .models import KYC, OTP, User, Role
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction

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
        fields = ['id', 'email', 'username', 'phone_number', 'role', 'password']
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
        fields = ['id', 'email', 'username', 'phone_number', 'role']

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.username = validated_data.get('username', instance.username)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.role = validated_data.get('role', instance.role)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()
        return instance
        
class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'username', 'phone_number', 'role']

    def create(self, validated_data):
        # Generate a random password
        password = get_random_string(length=12)

        # Start an atomic transaction
        with transaction.atomic():
            # Create the user with the generated password
            user = User.objects.create_user(**validated_data, password=password)
            
            # Try to send the password to the user's email
            try:
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




class CustomLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        user = authenticate(email=email, password=password)

        if user is None:
            raise serializers.ValidationError('Invalid credentials')

        # Generate OTP for email
        otp_instance, created = OTP.objects.get_or_create(user=user, is_verified=False)
        otp_instance.generate_otp()

        # Send OTP to email
        self.send_email_otp(user.email, otp_instance.otp_code)

        return {
            'message': f"OTP sent to your email : {email}. Please verify"
        }

    def send_email_otp(self, email, otp_code):
        subject = 'Your OTP Code'
        message = f'Your OTP code is {otp_code}.'
        from_email = settings.DEFAULT_FROM_EMAIL
        send_mail(subject, message, from_email, [email])


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
        refresh = RefreshToken.for_user(user)
        return {
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
    new_password = serializers.CharField()
from rest_framework import serializers
from .models import KYC

class KYCSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYC
        fields = ['user', 'document_type', 'document_file', 'confirmation', 'created_at', 'updated_at']


