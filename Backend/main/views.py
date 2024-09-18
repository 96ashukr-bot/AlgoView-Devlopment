from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
import time
from .models import *
from .serializers import *
import logging
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
logger = logging.getLogger(__name__)
UserModel = get_user_model()

# Role Views
class RoleListCreateView(generics.ListCreateAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    # permission_classes = [permissions.IsAuthenticated]

class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

# User Views
class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

#signup
class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        start_time=time.time()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Check if the role is provided in the validated data
        # role = serializer.validated_data.get('role', None)
        # if role and role.status != Role.ACTIVE:
        #     return Response({'detail': 'The selected role is not active.'}, status=status.HTTP_400_BAD_REQUEST)
        user = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        end_time = time.time()  # Record the end time
        execution_time = end_time - start_time  # Calculate the total time
        print(f"signup  API executed in {execution_time:.4f} seconds")
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
#login
class CustomLoginView(generics.GenericAPIView):
    serializer_class = CustomLoginSerializer
    def post(self, request, *args, **kwargs):
        start_time=time.time()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        end_time = time.time()  # Record the end time
        execution_time = end_time - start_time  # Calculate the total time
        print(f"Login API executed in {execution_time:.4f} seconds")  # Log the execution timee
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

#verify-otp via email
class OTPVerifyView(generics.GenericAPIView):
    serializer_class = OTPVerifySerializer

    def post(self, request, *args, **kwargs):
        start_time=time.time()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        end_time = time.time()  # Record the end time
        execution_time = end_time - start_time  # Calculate the total time
        print(f"verify otp API executed in {execution_time:.4f} seconds")
        logger.info(f"verify otp API executed in {execution_time:.4f} seconds")  # Log the execution timee
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

#change password
class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]  # Ensure only authenticated users can access this view

    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            if user.is_anonymous:
                return Response({'error': 'You must be logged in to change your password.'}, status=status.HTTP_401_UNAUTHORIZED)

            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)

            # Save the new password
            serializer.save()

            return Response({
                'message': 'Password successfully changed please login with new password.'
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({
                'error': 'Validation error',
                'details': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'error': 'Something went wrong while changing the password.',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Password Reset Views
class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    # permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data['email']
            user = UserModel.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            # reset_link = request.build_absolute_uri(
            #     f'/password-reset-confirm/?uidb64={uid}&token={token}'
            # )
            reset_link = f'http://localhost:3000/pages/authentication/reset-password/:{uid}/:{token}/:layout'
            subject = "Password Reset Request"
            print("reset_link",reset_link)
            message = (
                f"Hello,\n\n"
                f"You've requested a password reset. Click the link below to reset your password:\n"
                f"{reset_link}\n\n"
                f"If you did not request this, please ignore this email.\n\n"
                f"Best regards,\nYour Team"
            )
            from_email = settings.DEFAULT_FROM_EMAIL
            send_mail(subject, message, from_email, [email])
            return Response({'detail': 'Password reset link sent.'}, status=status.HTTP_200_OK)
        except UserModel.DoesNotExist:
            return Response({'detail': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uidb64 = serializer.validated_data['uidb64']
        token = serializer.validated_data['token']
        NewPassword = serializer.validated_data['NewPassword']
        
        try:
            uid = force_bytes(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'detail': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(NewPassword)
        user.save()
        
        return Response({'detail': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
    
class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer

class UserAssignRoleView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserAssignRoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        try:
            user = self.get_object()
            if not self.request.user.is_superuser:
                raise PermissionDenied("You do not have permission to perform this action.")
            return super().update(request, *args, **kwargs)
        except PermissionDenied as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({'detail': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserManagementView(generics.GenericAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # if not request.user.is_superuser:
            #     return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
            user_id = kwargs.get('pk')
            if user_id:
                user = self.get_object()
                serializer = self.get_serializer(user)
                return Response(serializer.data)
            else:
                users = self.get_queryset()
                serializer = self.get_serializer(users, many=True)
                return Response(serializer.data)
        except UserModel.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        try:
            if not request.user.is_superuser:
                return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, *args, **kwargs):
        try:
            # if not request.user.is_superuser:
            #     return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
            user = self.get_object()
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except UserModel.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, *args, **kwargs):
        try:
            if not request.user.is_superuser:
                return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
            user = self.get_object()
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserModel.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_update(self, serializer):
        if not self.request.user.is_superuser:
            raise PermissionDenied("You do not have permission to perform this action.")
        serializer.save()

    def perform_create(self, serializer):
        if not self.request.user.is_superuser:
            raise PermissionDenied("You do not have permission to perform this action.")
        serializer.save()
class UserProfileView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            serializer = UserProfileRetrieveSerializer(user)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, *args, **kwargs):
        user = request.user
        try:
            # Start transaction in case of complex updates (optional)
            with transaction.atomic():
                serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as ve:
            return Response({"validation_error": ve.detail}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class UserProfileView22(generics.UpdateAPIView):
    serializer_class = UserProfileUpdateSerializer
    queryset = User.objects.all()

    def get_object(self):
        return self.request.user    
class KYCListCreateView(generics.ListCreateAPIView):
    queryset = KYC.objects.all()
    serializer_class = KYCSerializer
    # permission_classes = [IsAuthenticated]  # Optional: ensure only logged-in users can access

    def perform_create(self, serializer):
        # If you're using a user relationship, pass the user here
        # serializer.save(user=self.request.user)
        serializer.save()
        
class KYCUpdateView(generics.UpdateAPIView):
    queryset = KYC.objects.all()
    serializer_class = KYCSerializer
    # permission_classes = [IsAuthenticated]  # Optional

    def perform_update(self, serializer):
        serializer.save()

class KYCDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = KYC.objects.all()
    serializer_class = KYCSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return KYC.objects.filter(user=self.request.user)