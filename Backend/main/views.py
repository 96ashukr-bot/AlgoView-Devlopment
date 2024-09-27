import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import requests
from rest_framework import generics, status, permissions
from rest_framework.permissions import IsAdminUser,IsAuthenticated
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
from django.contrib import messages
from pya3 import *
from decouple import config
from main.Alice_Blue_Api import ALICE_ORDER_URL,GET_ORDER_BOOK_URL,GET_TREAD_BOOK_URL

ALICE_API_KEY=config('ALICE_API_KEY')
USER_ID=config('USER_ID')

logger = logging.getLogger(__name__)
UserModel = get_user_model()

# gwt Role Views
class RoleListCreateView(generics.ListCreateAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    # permission_classes = [permissions.IsAuthenticated]

#delete role
class RoleDeleteView(generics.DestroyAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):
        role_id = kwargs.get('id')
        role = get_object_or_404(Role, id=role_id)
        role.delete()
        return Response({
            "status": "success",
            "message": f"Role with ID {role_id} has been deleted."
        }, status=status.HTTP_200_OK)    
class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    # permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

# User Views
class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # permission_classes = [permissions.IsAuthenticated]

#signup
class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        # start_time=time.time()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Check if the role is provided in the validated data
        # role = serializer.validated_data.get('role', None)
        # if role and role.status != Role.ACTIVE:
        #     return Response({'detail': 'The selected role is not active.'}, status=status.HTTP_400_BAD_REQUEST)
        user = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # end_time = time.time()  # Record the end time
        # execution_time = end_time - start_time  # Calculate the total time
        # print(f"signup  API executed in {execution_time:.4f} seconds")
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
#login
class CustomLoginView(generics.GenericAPIView):
    serializer_class = CustomLoginSerializer
    def post(self, request, *args, **kwargs):
        # start_time=time.time()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # end_time = time.time()  # Record the end time
        # execution_time = end_time - start_time  # Calculate the total time
        # print(f"Login API executed in {execution_time:.4f} seconds")  # Log the execution timee
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

#verify-otp via email
class OTPVerifyView(generics.GenericAPIView):
    serializer_class = OTPVerifySerializer

    def post(self, request, *args, **kwargs):
        # start_time=time.time()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # end_time = time.time()  # Record the end time
        # execution_time = end_time - start_time  # Calculate the total time
        # print(f"verify otp API executed in {execution_time:.4f} seconds")
        # logger.info(f"verify otp API executed in {execution_time:.4f} seconds")  # Log the execution timee
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
#resend otp
class ResendOTPView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')

        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get the user by email
            user = get_object_or_404(User, email=email)

            # Check if the last OTP is still valid and unverified
            otp_instance = OTP.objects.filter(user=user, is_verified=False).last()
            if otp_instance and not otp_instance.is_expired():
                return Response(
                    {"error": "A valid OTP already exists. Please check your email."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Generate and send a new OTP
            otp = OTP.objects.create(user=user)
            otp.generate_otp()
            # Send OTP via email
            self.send_email_otp(user.email, otp.otp_code)

            return Response(
                {"success": "A new OTP has been sent to your email."},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)

    def send_email_otp(self, email, otp_code):
        subject = 'Your OTP Code'
        message = f'Your OTP code is {otp_code}.'
        from_email = settings.DEFAULT_FROM_EMAIL
        send_mail(subject, message, from_email, [email]) 
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
class UserManagementView(APIView):
    # permission_classes = [IsAdminUser]  # Ensure only admins can create users
    def get(self, request, *args, **kwargs):
        users = User.objects.filter(is_superuser=False).order_by('id')
        serializer = UsergetSerializer(users, many=True)
        return Response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            messages.success(request, 'User created successfully.')
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=kwargs.get('pk'))
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(user, data=request.data, partial=True)  # partial=True allows updating only some fields
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'User updated successfully.')
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=kwargs.get('pk'))
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        user.delete()
        print(messages.success(request, 'User deleted successfully.'))
        return Response(status=status.HTTP_204_NO_CONTENT)
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
    
class PendingKYCListView(APIView):# Get all pending KYC requests
    def get(self, request, *args, **kwargs):
        pending_kycs = KYC.objects.filter(status='pending', is_verified=False)

        if pending_kycs.exists():
            serializer = KYCSerializer(pending_kycs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"message": "No pending KYC requests"}, status=status.HTTP_200_OK)

class KYCVerificationView(APIView):
    permission_classes = [IsAdminUser]  # Only admins can access KYC requests

    def post(self, request, kyc_id, *args, **kwargs):
        try:
            kyc = KYC.objects.get(id=kyc_id)
        except KYC.DoesNotExist:
            return Response({"detail": "KYC request not found."}, status=status.HTTP_404_NOT_FOUND)
        
        action = request.data.get('action')
        if not action:
            return Response({"detail": "Action is required (approve/reject)."}, status=status.HTTP_400_BAD_REQUEST)

        if action.lower() == 'approve':
            kyc.status = 'approved'
            kyc.is_verified = True  
            kyc.verified_by = request.user 
            kyc.save()
            return Response({
                "message": "KYC approved successfully.",
                "kyc_data": KYCSerializer(kyc).data
            }, status=status.HTTP_200_OK)
            
        elif action.lower() == 'reject':
            kyc.status = 'rejected'
            kyc.is_verified = False  
            kyc.save()  
            return Response({
                "message": "KYC rejected.",
                "kyc_data": KYCSerializer(kyc).data
            }, status=status.HTTP_200_OK)

        else:
            return Response({"detail": "Invalid action. Use 'approve' or 'reject'."}, status=status.HTTP_400_BAD_REQUEST)

# Global variables to store session ID and expiration time
SESSION_ID = None
SESSION_EXPIRATION = None

# Place an order using Alice Blue API
def place_order(alert_data, session_id):
    """Place an order using Alice Blue API"""
    order_payload = {
        "complexty": "regular",
        "discqty": "0",
        "exch": "NSE",
        "pCode": alert_data.get("productType", "MIS"),
        "prctyp": "MKT",
        "price": alert_data.get("strikePrice", "0"),
        "qty": alert_data.get("Lot", 1),
        "ret": "DAY",
        "symbol_id": alert_data.get("symbol_id"),
        "trading_symbol": alert_data.get("trading_symbol"),
        "transtype": alert_data.get("buy_sell").upper(),
        "trigPrice": alert_data.get("triggerPrice", ""),
        "orderTag": alert_data.get("orderTag", "order1")
    }
    sessionID = session_id.get('sessionID')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {USER_ID} {sessionID}'  # Use Bearer token for authentication
    }

    try:
        response = requests.post(ALICE_ORDER_URL, headers=headers, data=json.dumps([order_payload]))
        response.raise_for_status()
        # After successfully placing the order, save the order details in the log
        save_order_log(alert_data)
        return response  # Return the response as JSON
    except requests.RequestException as req_err:
        return {"status": "error", "message": f"Request exception: {str(req_err)}"}
    except Exception as e:
        return {"status": "error", "message": f"An error occurred: {str(e)}"}

from django.utils import timezone  # Django's timezone utilities
from datetime import datetime
def save_order_log(alert_data):
    """Save order details into the log table"""
    try:
        # Save the order log to the database
        OrderLog.objects.create(
            signal_time=timezone.now(),  # You can change this to the actual signal time
            order_type=alert_data.get('Type').upper(),  # 'LX' or 'LE'
            symbol=alert_data.get('trading_symbol'),  # Symbol
            price=alert_data.get('strikePrice'),  # Order price
            strategy=alert_data.get('strategy', 'Unknown')  # Strategy used
        )
    except Exception as e:
        print(f"Failed to save order log: {str(e)}")

from datetime import datetime, timedelta  # For getting current date and time
# Get or regenerate Alice Blue session ID
def get_or_regenerate_session_id(USER_ID, ALICE_API_KEY):
    global SESSION_ID, SESSION_EXPIRATION
    # Check if the session ID is expired or not set
    current_time = datetime.now()
    
    # Check if the session ID is expired or not set
    if SESSION_ID is None or SESSION_EXPIRATION is None or current_time >= SESSION_EXPIRATION:
        print("Session ID expired or not found. Regenerating...")
        alice = Aliceblue(user_id=USER_ID, api_key=ALICE_API_KEY)
        SESSION_ID = alice.get_session_id(alice)
        
        # Assume the session expires in 24 hours (86400 seconds)
        SESSION_EXPIRATION = current_time + timedelta(seconds=86400)
        print(f"New session ID generated: {SESSION_ID}")
    else:
        print("Using existing session ID........")
    
    return SESSION_ID

# Webhook 
class TradingViewWebhook(APIView):
    def post(self, request, *args, **kwargs):
        try:
            alert_data = request.data
            print(f"Received alert: {alert_data}")
            # Get or regenerate session ID
            session_id = get_or_regenerate_session_id(USER_ID, ALICE_API_KEY)
            print(f"Session ID:")

            # Place the order using the session ID
            order_response = place_order(alert_data, session_id)
            return Response({
                'order_resp': order_response.json()
            },order_response.status_code )

        except json.JSONDecodeError:
            return Response({
                "status": "error",
                "message": "Invalid JSON received."
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Get Alice-Blue orders  GET_ORDER_BOOK_URL
class GetAliceOrderBook(APIView):
    def get(self, request, *args, **kwargs):
        # Get or regenerate the session ID
        session_id_response = get_or_regenerate_session_id(USER_ID, ALICE_API_KEY)
        # Extract sessionID from the response
        sessionID = session_id_response.get('sessionID') if isinstance(session_id_response, dict) else None  
        if not sessionID:
            return Response({
                "status": "error",
                "message": "Failed to obtain a valid session ID."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {USER_ID} {sessionID}'  # Assuming session ID is used this way
        }
        try:
            # Send a GET request to the order book endpoint
            response = requests.get(GET_ORDER_BOOK_URL, headers=headers)
            response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)

            # Return the successful response data
            return Response({
                "status": "success",
                "data": response.json()
            }, status=status.HTTP_200_OK)

        except requests.RequestException as req_err:
            # Handle request exceptions such as timeouts, bad responses, etc.
            return Response({
                "status": "error",
                "message": f"Request error: {str(req_err)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            # Handle any other exceptions
            return Response({
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#Get trad history data GET_TREAD_BOOK_URL
class GetAliceTreadBook(APIView):
    def get(self, request, *args, **kwargs):
        # Get or regenerate the session ID
        session_id_response = get_or_regenerate_session_id(USER_ID, ALICE_API_KEY)
        # Extract sessionID from the response
        sessionID = session_id_response.get('sessionID') if isinstance(session_id_response, dict) else None  
        if not sessionID:
            return Response({
                "status": "error",
                "message": "Failed to obtain a valid session ID."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {USER_ID} {sessionID}'  # Assuming session ID is used this way
        }
        try:
            # Send a GET request to the order book endpoint
            response = requests.get(GET_TREAD_BOOK_URL, headers=headers)
            response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)

            # Return the successful response data
            return Response({
                "status": "success",
                "data": response.json()
            }, status=response.status_code)

        except requests.RequestException as req_err:
            # Handle request exceptions such as timeouts, bad responses, etc.
            return Response({
                "status": "error",
                "message": f"Request error: {str(req_err)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            # Handle any other exceptions
            return Response({
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OrderLogListView(APIView):
    def get(self, request, *args, **kwargs):
        # Fetch all the order logs from the database
        order_logs = OrderLog.objects.all()
        
        # Serialize the data
        serializer = OrderLogSerializer(order_logs, many=True)
        
        # Return the serialized data as a JSON response
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    