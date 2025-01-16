import csv
from decimal import Decimal
import json
import os
from amqp import NotFound
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
from rest_framework.generics import ListAPIView,UpdateAPIView
from main.angleapi import get_token_details, place_Angle_order
from main.dematemodule import trading_Symbol_sum
from main.permissions import  IsAdminRole
from main.tasks import send_kyc_email_async, send_trade_email_async
from rest_framework import status
from django.utils.timezone import make_aware
from pytz import timezone as pytz_timezone
from main.upstock import place_upstox_orders
from main.zerodha import place_zerodha_orders
from .models import *
from .serializers import *
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from django.contrib import messages
from pya3 import *
from decouple import config
from main.Alice_Blue_Api import ALICE_ORDER_URL,GET_ORDER_BOOK_URL,GET_TREAD_BOOK_URL, is_market_open, place_alice_orders, save_trade_order_history
from rest_framework.pagination import PageNumberPagination        
from main.email import EmailService
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.db.models import Q
from django.db.models import Count, Prefetch
import pandas as pd
from datetime import datetime
from django.core.cache import cache
import pyotp
# from SmartApi import SmartConnect
# from SmartApi.smartExceptions import DataException
# from time import sleep
import numpy as np
import pytz

USER_ID=config('USER_ID')
ALICE_API_KEY=config('ALICE_API_KEY')
import logging
logger = logging.getLogger('main')
UserModel = get_user_model()
#email parmas

support_email=settings.DEFAULT_FROM_EMAIL
contact_number=settings.CONTACT_NUM
login_link=settings.LOGIN_LINK
help_center_link=settings.HELP_CENTER_LINK
company_website=settings.COMPANY_WEBSITE    
# get Role Views
class RoleListCreateView(generics.ListCreateAPIView):
    pagination_class = None
    queryset=Role.objects.all().order_by('-id')
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]
class GetRoleListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            roles = Role.objects.filter(Q(name__iexact='Sub-Admin') | Q(name__iexact='Admin')).order_by('-id')
            serializer = RoleSerializer(roles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Role.DoesNotExist:
            logger.error("No roles found.")
            return Response({
                "status": "error",
                "message": "No roles found."
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.exception("An error occurred while fetching roles.")
            return Response({
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#delete role
class RoleDeleteView(generics.DestroyAPIView):
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]
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
    pagination_class = None
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]

# User Views create
class UserListCreateView(generics.ListCreateAPIView):
    pagination_class = None
    queryset = User.objects.filter(type_of_user='is_user').order_by('-id')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        # start_time=time.time()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
#login
class CustomLoginView(generics.GenericAPIView):
    pagination_class = None
    serializer_class = CustomLoginSerializer
    def post(self, request, *args, **kwargs):
        # start_time=time.time()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # end_time = time.time()  # Record the end time
        # execution_time = end_time - start_time  # Calculate the total time
        # print(f"Login API executed in {execution_time:.4f} seconds")  # Log the execution timee
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
#logout api
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def post(self, request):
        # Get user's refresh token from request data (passed by frontend)
        refresh_token = request.data.get('refresh_token')
        
        try:
            # Blacklist the refresh token (if using Simple JWT Blacklisting)
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Log the user's logout time in the UserActivityLog
            session_key = request.session.session_key
            try:
                activity_log = UserActivityLog.objects.filter(user=request.user,session_key=session_key).latest('last_login_time')
                activity_log.mark_logout()
            except UserActivityLog.DoesNotExist:
                pass  # If no login entry exists, skip silently
            
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    
#verify-otp via email
class OTPVerifyView(generics.GenericAPIView):
    serializer_class = OTPVerifySerializer
    pagination_class = None
    def post(self, request, *args, **kwargs):
        # start_time=time.time()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # end_time = time.time()  # Record the end time
        # execution_time = end_time - start_time  # Calculate the total time
        # print(f"verify otp API executed in {execution_time:.4f} seconds")
        # logger.info(f"verify otp API executed in {execution_time:.4f} seconds")  # Log the execution timee
        # return Response(serializer.validated_data, status=status.HTTP_200_OK)
        # Get the user from the serializer
        # Get the user ID or email from the serializer (not the full user object)
        user_id = serializer.validated_data['user_id']
        email = serializer.validated_data['email']

        # Check if the user has completed eKYC
        kyc_exists = KYC.objects.filter(user_id=user_id).exists()

        ekyc_status = kyc_exists  # True if KYC record exists, otherwise False

        # Add the eKYC status to the response
        response_data = serializer.validated_data
        response_data['ekyc_status'] = ekyc_status

        return Response(response_data, status=status.HTTP_200_OK)
#resend otp
class ResendOTPView(APIView):
    pagination_class = None
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
    pagination_class = None
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]  # Ensure only authenticated users can access this view

    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            if user.is_anonymous:
                return Response({'error': 'You must be logged in to change your password.'}, status=status.HTTP_401_UNAUTHORIZED)

            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            # Check if the user has completed eKYC
            kyc_exists = KYC.objects.filter(user_id=user.id).exists()

            ekyc_status = kyc_exists  # True if KYC record exists, otherwise False
            # Save the new password
            serializer.save()
            role_data = {
                'role_id': user.role.id if user.role else None,
                'role_name': user.role.name if user.role else None,
                'role_status': user.role.status if user.role else None
            }
            return Response({
                'user':user.id,
                'role':role_data,
                'ekyc_status':ekyc_status,
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
    pagination_class = None

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
            
            # reset_link = f'http://103.120.178.54:4000/pages/authentication/reset-password/:{uid}/:{token}/:layout'
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
#user assign role api    
class UserAssignRoleView(generics.UpdateAPIView):
    pagination_class = None
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated,  ] 
    serializer_class = UserAssignRoleSerializer
    def update(self, request, *args, **kwargs):
        try:
            user = self.get_object()  # Get the user by ID (provided in the URL)
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#pagination of users list
class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10  # Default page size
    page_size_query_param = 'page_size'  # Allows the client to set the page size dynamically
    max_page_size = 100  # Max limit for page size to avoid performance issues
    page_query_param = 'page_number'  # Allows the client to set the page number
class GetUser(APIView):
    permission_classes = [permissions.IsAuthenticated,  ]
    def get(self, request, pk, *args, **kwargs): 
        try:
            user = User.objects.get(pk=pk)  
            serializer = UserSerializer(user)  
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
# All sub-admins list     
class SubadminsView(APIView):
    permission_classes = [permissions.IsAuthenticated,  ]
    def get(self, request, *args, **kwargs):
        user = request.user 
        try:
        #     if user.role and user.role.name == 'Super-Admin':
            subadmin = User.objects.filter(role__name='Sub-Admin').order_by('-id')
            serializer = UserSerializer(subadmin,many=True) 
        except User.DoesNotExist:
            return Response({"detail": "subadmins not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.data)
    
#user crud api for admin
class UserManagementView(APIView):
    permission_classes = [permissions.IsAuthenticated,  ]
    def get(self, request, *args, **kwargs):
        user = request.user 
        if user.role and user.role.name == 'Super-Admin':
            # Get all Sub-Admins (with role 'Sub-Admin') and prefetch their clients
            users = User.objects.filter(role__name='Sub-Admin').annotate(
                client_count=Count('assigned_users')
            ).prefetch_related(
                Prefetch('assigned_users', queryset=User.objects.all(), to_attr='assigned_users_list')
            ).order_by('-id')
        else:
            # Get Sub-Admins that the logged-in user has created, with client count and client list
            users = User.objects.filter(role__name='Sub-Admin', id=user.id)
            # .annotate(client_count=Count('assigned_users')).prefetch_related(
            #     Prefetch('assigned_users', queryset=User.objects.all(), to_attr='assigned_users_list') ).order_by('-id')
            logger.info("Admin:::{user.role.name}")
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(users, request)
        serializer = UserSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    # def get(self, request, *args, **kwargs):
    #     users = User.objects.all().order_by('id')
    #     paginator = CustomPageNumberPagination()
    #     result_page = paginator.paginate_queryset(users, request)
    #     serializer = UserSerializer(result_page, many=True)
    #     return paginator.get_paginated_response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        # Generate a random password
        password = get_random_string(length=12)
        # Create user with the autogenerated password
        user = User.objects.get(id=request.user.id)
        role=Role.objects.get(name='Sub-Admin')
        serializer = NewUserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(created_by=request.user,role=role) 
            # user.external_user = False
            user.type_of_user='is_user'
            user.set_password(password)  
            user.save() 
            
            # Send the password via email
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
            print("sub-admin or client password---",password)
            # EmailService.send_password_email(user.email, password,user.firstName,login_link,support_email,help_center_link,company_website,contact_number)
            
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def put(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=kwargs.get('pk'))
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = NewUserCreateSerializer(user, data=request.data, partial=True)  # partial=True allows updating only some fields
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'User updated successfully.')
            return Response({"msg":"User updated successfully.",'data':serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=kwargs.get('pk'))
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        user.delete()
        print(messages.success(request, 'User deleted successfully.'))
        return Response({"msg": "User deleted successfully."},status=status.HTTP_204_NO_CONTENT)
        
#sub-admin user profile api crud oprations        
class UserProfileView(APIView):
    pagination_class = None
    permission_classes = [IsAuthenticated]
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
                print("____________",request.data)
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

# get kyc list 
class GetKYCView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = None
    def get(self, request, *args, **kwargs):
        user = request.user
        
        try:
            kyc = KYC.objects.get(user=user)
            serializer = KYCSerializer(kyc)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except KYC.DoesNotExist:
            return Response({'message': 'KYC not found for this user.'}, status=status.HTTP_404_NOT_FOUND)  
class GetKYCByIdView(APIView):
    # permission_classes = [IsAuthenticated]
    pagination_class = None
    def get(self, request,pk, *args, **kwargs):
        try:
            kyc = KYC.objects.get(pk=pk)
            serializer = KYCSerializer(kyc)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except KYC.DoesNotExist:
            return Response({'message': 'KYC not found.'}, status=status.HTTP_404_NOT_FOUND)  
                
#kyc update create 
class CreateOrUpdateKYCView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = None
    def post(self, request, *args, **kwargs):
        user = request.user
        kyc, created = KYC.objects.get_or_create(user=user)

        # If it's an existing KYC, update it with the provided data
        serializer = KYCSerializer(kyc, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            message = "KYC created" if created else "KYC updated"
            return Response({
                "status": "success",
                "message": message,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#pending kyc list for admin    
class PendingKYCListView(APIView):# Get all pending KYC requests
    permission_classes = [permissions.IsAuthenticated, ] 
    # pagination_class = None
    def get(self, request, *args, **kwargs):
        pending_kycs = KYC.objects.all().order_by('-id')
        if pending_kycs.exists():
            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(pending_kycs, request)
            serializer = KYCSerializer(result_page, many=True)
            # serializer = KYCSerializer(pending_kycs, many=True)
            # return Response(serializer.data, status=status.HTTP_200_OK)
            return paginator.get_paginated_response(serializer.data)
        else:
            return Response({"message": "No any KYC requests"}, status=status.HTTP_200_OK)

#kyc verification by admin
class KYCVerificationView(APIView):
    permission_classes = [permissions.IsAuthenticated, ]  # Only admins can access KYC requests
    def post(self, request, kyc_id, *args, **kwargs):
        try:
            kyc = KYC.objects.get(id=kyc_id)
        except KYC.DoesNotExist:
            return Response({"detail": "KYC request not found."}, status=status.HTTP_404_NOT_FOUND)
        
        action = request.data.get('action')
        if not action:
            return Response({"detail": "Action is required (approve/reject)."}, status=status.HTTP_400_BAD_REQUEST)
        user_email = kyc.user.email 
        from_email = settings.DEFAULT_FROM_EMAIL,
        reason = request.data.get('reason', 'No reason provided')
        if action.lower() == 'approve':
            kyc.status = 'approved'
            kyc.is_verified = True  
            kyc.verified_by = request.user 
            kyc.save()
            # Send approval email
            send_kyc_email_async.delay(user_email, from_email, kyc.user.firstName, 'approve', reason)
            # Send approval email
            # send_mail(
            #     subject="Your KYC has been approved",
            #     message="Congratulations! Your KYC request has been approved.",
            #     from_email=from_email,
            #     recipient_list=[user_email],
            #     fail_silently=False,
            # )
            return Response({
                "message": "KYC approved successfully.",
                "kyc_data": KYCSerializer(kyc).data
            }, status=status.HTTP_200_OK)
            
        elif action.lower() == 'reject':
            kyc.status = 'rejected'
            kyc.is_verified = False  
            kyc.save() 
            # Send rejection email
            send_kyc_email_async.delay(user_email, from_email, kyc.user.firstName, 'reject', reason)
               
            return Response({
                "message": "KYC rejected.",
                "kyc_data": KYCSerializer(kyc).data
            }, status=status.HTTP_200_OK)

        else:
            return Response({"detail": "Invalid action. Use 'approve' or 'reject'."}, status=status.HTTP_400_BAD_REQUEST)



#store sssion logs last login
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    pagination_class = None
    ip_address = request.META.get('REMOTE_ADDR')
    session_key = request.session.session_key
    UserActivityLog.objects.create(
        user=user,
        last_login_time=timezone.now(),
        ip_address=ip_address,
        session_key=session_key
    )
#last logout time
@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    pagination_class = None
    session_key = request.session.session_key
    try:
        activity_log = UserActivityLog.objects.filter(user=user, session_key=session_key).latest('last_login_time')
        activity_log.mark_logout()
    except UserActivityLog.DoesNotExist:
        pass  
class UserActivityLogListView(ListAPIView):
    pagination_class = None
    queryset = UserActivityLog.objects.all()
    serializer_class = UserActivityLogSerializer
    permission_classes = [IsAuthenticated]  # Change if you want different permissions
    def get_queryset(self):
        user = self.request.user
        return UserActivityLog.objects.filter(user=user)  # Optional: filter logs by logged-in user    

class UserActivityLogListView(ListAPIView):
    pagination_class = None
    serializer_class = UserActivityLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return activity logs for the logged-in user
        return UserActivityLog.objects.filter(user=self.request.user).order_by('-last_login_time')

#last login api
class LastLoginActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            last_two_login_activities = UserActivityLog.objects.filter(
                user=request.user, action_type='login'
            ).order_by('-last_login_time')[:2]
            if last_two_login_activities:
                if len(last_two_login_activities) == 1:
                    last_login_activity = last_two_login_activities[0]
                else:
                    # If there are at least two, get the second latest
                    last_login_activity = last_two_login_activities[1]
            response_data = {
                'last_login_time': last_login_activity.last_login_time,
                'last_ip': last_login_activity.ip_address,
                'session_key': last_login_activity.session_key,
                # 'is_logged_out': last_login_activity.logout_time is not None,
            }

            return Response(response_data)
        except UserActivityLog.DoesNotExist:
            return Response({"error": "No login activity found."}, status=404)
#get all city names
class Get_city_data(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs): 
        try:
            city = cities.objects.all()[:10]
            serializer = CitesSerializer(city, many=True)
        except cities.DoesNotExist:
            return Response({"error": "city not found."}, status=404)   
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
#search city name
class CitySearchView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        query = request.GET.get('city', '')  
        if query:
            city = cities.objects.filter(name__icontains=query)
            serializer = CitesSerializer(city, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response([], status=status.HTTP_200_OK)
#get all states name
class GetStatesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        try:
            state=State.objects.all()    
            ser=StatesSerializers(state,many=True)
        except State.DoesNotExist:
            return Response({"error": "state not found."}, status=404)  
        return Response({
            "status":"sucess",
            "data":ser.data }, status=status.HTTP_200_OK)
class SearchStatesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        query = request.GET.get('state', '')  
        if query:
            city = State.objects.filter(name__icontains=query)
            serializer = StatesSerializers(city, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response([], status=status.HTTP_200_OK)      
#segment crud apis
class SegmentlistAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        try:
            segments = Segment.objects.all().order_by('-id')
            serializer = SegmentSerializer(segments, many=True)
        except Segment.DoesNotExist:
            return Response({"error": "Segments not found."}, status=404)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
class SegmentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    # def get(self, request, *args, **kwargs):
    #     try:
    #         segments = Segment.objects.all()
    #         serializer = SegmentSerializer(segments, many=True)
    #     except Segment.DoesNotExist:
    #         return Response({"error": "Segments not found."}, status=404)
        
    #     return Response(serializer.data, status=status.HTTP_200_OK)
    def get(self, request, *args, **kwargs):
        segments = Segment.objects.all().order_by('-id')
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(segments, request)
        serializer = SegmentSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        serializer = SegmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            segment = Segment.objects.get(pk=kwargs.get('pk'))
        except Segment.DoesNotExist:
            return Response({"detail": "Segment not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = SegmentSerializer(segment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'Segment updated successfully.')
            return Response({"msg": "Segment updated successfully.", 'data': serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            segment = Segment.objects.get(pk=kwargs.get('pk'))
            segment.delete()
            return Response({"msg": "Segment deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Segment.DoesNotExist:
            return Response({"detail": "Segment not found."}, status=status.HTTP_404_NOT_FOUND)
class CategorylistAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            category_list = categories.objects.all().order_by('-id')
            serializer = CategorySerializer(category_list, many=True)
        except categories.DoesNotExist:
            return Response({"error": "Categories not found."}, status=404)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

class CategoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # def get(self, request, *args, **kwargs):
    #     try:
    #         category_list = categories.objects.all()
    #         serializer = CategorySerializer(category_list, many=True)
    #     except categories.DoesNotExist:
    #         return Response({"error": "Categories not found."}, status=404)
        
    #     return Response(serializer.data, status=status.HTTP_200_OK)
    def get(self, request, *args, **kwargs):
        category_list = categories.objects.all().order_by('-id')
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(category_list, request)
        serializer = CategorySerializer(result_page, many=True)
        
        return paginator.get_paginated_response(serializer.data)
    def post(self, request, *args, **kwargs):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            category = categories.objects.get(pk=kwargs.get('pk'))
        except categories.DoesNotExist:
            return Response({"detail": "Category not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'Category updated successfully.')
            return Response({"msg": "Category updated successfully.", 'data': serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            category = categories.objects.get(pk=kwargs.get('pk'))
            category.delete()
            return Response({"msg": "Category deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except categories.DoesNotExist:
            return Response({"detail": "Category not found."}, status=status.HTTP_404_NOT_FOUND)


class LicenseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            license_list = License.objects.all().order_by('-id')
            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(license_list, request)
            serializer = LicenseSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except License.DoesNotExist:
            return Response({"error": "Licenses not found."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, *args, **kwargs):
        serializer = LicenseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            license_obj = License.objects.get(pk=kwargs.get('pk'))
        except License.DoesNotExist:
            return Response({"detail": "License not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = LicenseSerializer(license_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "License updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            license_obj = License.objects.get(pk=kwargs.get('pk'))
            license_obj.delete()
            return Response({"msg": "License deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except License.DoesNotExist:
            return Response({"detail": "License not found."}, status=status.HTTP_404_NOT_FOUND)


#serices crud
class ServicelistAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            services = Services.objects.all().order_by('-id')
            serializer = ServiceSerializer(services, many=True)
        except Services.DoesNotExist:
            return Response({"error": "serices not found."}, status=404)
        return Response(serializer.data, status=status.HTTP_200_OK) 
class ServiceAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        services = Services.objects.all().order_by('-id')
        paginator = CustomPageNumberPagination()  
        result_page = paginator.paginate_queryset(services, request)  
        serializer = ServiceSerializer(result_page, many=True)  
        return paginator.get_paginated_response(serializer.data)  
    
    def post(self, request, *args, **kwargs):
        serializer = ServiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Service created successfully.", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            service = Services.objects.get(pk=kwargs.get('pk'))
        except Services.DoesNotExist:
            return Response({"detail": "Service not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ServiceSerializer(service, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Service updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, *args, **kwargs):
        try:
            service = Services.objects.get(pk=kwargs.get('pk'))
            service.delete()
            return Response({"msg": "Services deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Services.DoesNotExist:
            return Response({"detail": "Services not found."}, status=status.HTTP_404_NOT_FOUND)
#group services api
class GroupServicelistView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            logger.debug("GroupServiceView GET request received")  
            group_ser = GroupService.objects.all().order_by('-id')
            # Serialize the data
            serializer = GroupServiceSerializer(group_ser, many=True)
            serialized_data = serializer.data
            for item in serialized_data:
                json_data = item.get('json_data', None)
                if json_data is None:
                    json_data = []
                service_names = [entry.get('ServiceName') for entry in json_data if isinstance(entry, dict)]
                item['service_count'] = len(service_names)
                
            return Response(serialized_data, status=200)
        except GroupService.DoesNotExist:
            logger.error("GroupService not found.")   
            return Response({"error": "GroupService not found."}, status=404)
        except Exception as e:
            logger.critical("An unexpected error occurred: %s", str(e))
            return Response({"error": "An unexpected error occurred."}, status=500)

class GroupServiceView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            logger.debug("GroupServiceView GET request received")  # DEBUG message
            
            group_ser = GroupService.objects.all().order_by('-id')
            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(group_ser, request)
            
            # Modify the serialized data to include `service_count`
            serializer = GroupServiceSerializer(result_page, many=True)
            serialized_data = serializer.data

            # Add `service_count` to each item in the serialized data
            for item in serialized_data:
                json_data = item.get('json_data', None)
                
                # If json_data is None, set it to an empty list
                if json_data is None:
                    json_data = []
                service_names = [entry.get('ServiceName') for entry in json_data if isinstance(entry, dict)]
                item['service_count'] = len(service_names)

            # return paginator.get_paginated_response(serialized_data)
        except GroupService.DoesNotExist:
            logger.error("GroupService not found.")   
            return Response({"error": "GroupService not found."}, status=404)

        except Exception as e:
            logger.critical("An unexpected error occurred: %s", str(e))  
            return Response({"error": "An unexpected error occurred."}, status=500)

        return paginator.get_paginated_response(serialized_data)

    def post(self, request, *args, **kwargs):
        serializer = GroupServiceUpdateSerializer(data=request.data)
        if serializer.is_valid():
            group_service=serializer.save()
            group_service=GroupServiceSerializer(group_service)
            return Response(group_service.data, status=status.HTTP_201_CREATED)
        else:
            # Print errors to debug
            print(serializer.errors)  
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            group_service = GroupService.objects.get(pk=kwargs.get('pk'))
        except GroupService.DoesNotExist:
            return Response({"detail": "GroupService not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = GroupServiceUpdateSerializer(group_service, data=request.data, partial=True)
        if serializer.is_valid():
            group_services=serializer.save()
            ser=GroupServiceSerializer(group_services)
            return Response({"msg": "GroupService updated successfully.", 'data': ser.data}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, *args, **kwargs):
        try:
            service = GroupService.objects.get(pk=kwargs.get('pk'))
            service.delete()
            return Response({"msg": "GroupService deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except GroupService.DoesNotExist:
            return Response({"detail": "GroupService not found."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, *args, **kwargs):#delete json data 
        try:
            group_service = GroupService.objects.get(pk=kwargs.get('pk'))  # Get the group service by ID
        except GroupService.DoesNotExist:
            return Response({"detail": "GroupService not found."}, status=status.HTTP_404_NOT_FOUND)

        s_no_to_delete = request.data.get('s_no', None)

        if s_no_to_delete is None:
            return Response({"error": "S.No is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Filter out the entry from `json_data` that matches the `S.No`
        updated_json_data = [
            entry for entry in group_service.json_data 
            if entry.get('S.No') != s_no_to_delete
        ]

        # If no entry was removed, return an error
        if len(updated_json_data) == len(group_service.json_data):
            return Response({"error": f"Entry with S.No {s_no_to_delete} not found."}, status=status.HTTP_404_NOT_FOUND)

        # Update the `json_data` field and save the updated object
        group_service.json_data = updated_json_data
        group_service.save()

        return Response({
            "msg": f"Entry with S.No '{s_no_to_delete}' deleted successfully.",
            "updated_data": GroupServiceSerializer(group_service).data
        }, status=status.HTTP_200_OK)
#api for update json data inside group service
class GroupServiceJsonUpdateView(APIView):
    def patch(self, request, *args, **kwargs):
        try:
            group_service = GroupService.objects.get(pk=kwargs.get('pk'))  # Get the group service by ID
        except GroupService.DoesNotExist:
            return Response({"detail": "GroupService not found."}, status=status.HTTP_404_NOT_FOUND)

        # The identifier of the entry to be updated, in this case, 'S.No'
        s_no_to_update = request.data.get('s_no', None)
        update_data = request.data.get('update_data', None)

        if s_no_to_update is None:
            return Response({"error": "S.No is required."}, status=status.HTTP_400_BAD_REQUEST)

        if update_data is None:
            return Response({"error": "Update data is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Flag to check if entry is found
        entry_updated = False

        # Iterate through the json_data and update the relevant entry
        updated_json_data = []
        for entry in group_service.json_data:
            if entry.get('S.No') == s_no_to_update:
                entry_updated = True
                # Update the entry with new data
                entry.update(update_data)
            updated_json_data.append(entry)

        # If no entry was updated, return an error
        if not entry_updated:
            return Response({"error": f"Entry with S.No {s_no_to_update} not found."}, status=status.HTTP_404_NOT_FOUND)

        # Update the `json_data` field and save the updated object
        group_service.json_data = updated_json_data
        group_service.save()

        return Response({
            "msg": f"Entry with S.No '{s_no_to_update}' updated successfully.",
            "updated_data": GroupServiceSerializer(group_service).data
        }, status=status.HTTP_200_OK)

#get services inside group by id
class GetGroupServiceAPIView(APIView):
    def get(self, request, pk, *args, **kwargs): 
        try:
            user = GroupService.objects.get(pk=pk)  
            serializer = GroupServiceSerializer(user)
        except GroupService.DoesNotExist:
            return Response({"detail": "service not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.data, status=status.HTTP_200_OK)       

class Group_ServicesQtyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id, *args, **kwargs):
        try:
            logger.debug("GroupServiceDetailView GET request received for ID: %s", id)

            # Retrieve the GroupService object based on the provided ID
            group_service = GroupService.objects.get(id=id)
            
            # Extract the relevant fields
            json_data = group_service.json_data
            formatted_data = [
                {
                    "Qty": entry.get("Qty"),
                    "ServiceName": entry.get("ServiceName")
                }
                for entry in json_data if isinstance(entry, dict)
            ]
            
            # Prepare the response
            response_data = {
                "id": group_service.id,
                "group_name": group_service.group_name,
                "json_data": formatted_data
            }

            logger.info("Response prepared successfully for ID: %s", id)
            return Response(response_data, status=status.HTTP_200_OK)
        
        except GroupService.DoesNotExist:
            logger.error("GroupService with ID %s not found.", id)
            return Response({"error": "GroupService not found."}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.critical("An unexpected error occurred: %s", str(e))
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class StrategyAPIView(APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        strategies = Strategies.objects.all().order_by('-id')
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(strategies, request)
        serializer = GetStrategySerializer(result_page, many=True)
        # logging.info("strategy of data>>>>>",serializer.data)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = StrategySerializer(data=request.data)
        if serializer.is_valid():
            strategy_instance=serializer.save()
             # Now use the saved instance to serialize the data
            get_strategy_serializer = GetStrategySerializer(strategy_instance)

            return Response({"detail": "Strategy created successfully.", "data": get_strategy_serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, *args, **kwargs):
        try:
            strategy = Strategies.objects.get(pk=kwargs.get('pk'))
            # print("Request data:", request.data, indent=4)  # Convert request data to JSON string for printing

        except Strategies.DoesNotExist:
            return Response({"detail": "Strategy not found."}, status=status.HTTP_404_NOT_FOUND)
           
        serializer = StrategySerializer(strategy, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Strategy updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            strategy = Strategies.objects.get(pk=kwargs.get('pk'))
            strategy.delete()
            return Response({"msg": "Strategy deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Strategies.DoesNotExist:
            return Response({"detail": "Strategy not found."}, status=status.HTTP_404_NOT_FOUND)
        
class GetStrategyAPIView(APIView):
    # permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk, *args, **kwargs): 
        try:
            user = Strategies.objects.get(pk=pk)  
            serializer = GetStrategySerializer(user)  
        except Strategies.DoesNotExist:
            return Response({"detail": "Strategy not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.data, status=status.HTTP_200_OK)        
class BrokerView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, *args, **kwargs):
        broker_id = kwargs.get('pk', None)
        
        if broker_id:
            try:
                broker = Broker.objects.get(pk=broker_id)
                serializer = GetBrokerSerializer(broker)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Broker.DoesNotExist:
                return Response({"detail": "Broker not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            brokers = Broker.objects.all()
            serializer = GetBrokerSerializer(brokers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = GetBrokerSerializer(data=request.data)
        if serializer.is_valid():
            broker = serializer.save()
            return Response(GetBrokerSerializer(broker).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        broker_id = kwargs.get('pk', None)
        if not broker_id:
            return Response({"detail": "Broker ID is required for updating."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            broker = Broker.objects.get(pk=broker_id)
        except Broker.DoesNotExist:
            return Response({"detail": "Broker not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetBrokerSerializer(broker, data=request.data)
        if serializer.is_valid():
            broker = serializer.save()
            return Response(GetBrokerSerializer(broker).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        broker_id = kwargs.get('pk', None)
        if not broker_id:
            return Response({"detail": "Broker ID is required for deletion."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            broker = Broker.objects.get(pk=broker_id)
            broker.delete()
            return Response({"detail": "Broker deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Broker.DoesNotExist:
            return Response({"detail": "Broker not found."}, status=status.HTTP_404_NOT_FOUND)
import time

class ClientFilterView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user 
        if user.role and user.role.name.lower() == 'super-admin' or user.role.name =='Super-Admin':
            clients = User.objects.filter(type_of_user='is_client', is_client=True).order_by('-id')
        # elif user.role and user.role.name.lower() == 'sub-admin' or user.role.name=='Sub-Admin':
            # print("sub-admin.........")
            # clients = User.objects.filter(assigned_client=user).order_by('-id')
        else:
            clients = User.objects.filter(Q(type_of_user='is_client') & (Q(created_by=user) 
            | Q(assigned_client=user))).order_by('-id')
            # clients = User.objects.filter(type_of_user='is_client',is_client=True, created_by=user).order_by('-id')
                # Apply additional filters based on query parameters
        license_type = request.query_params.get('client_type') 
        trading_status = request.query_params.get('trading_type')  
        # broker_type = request.query_params.get('broker_type') 

        if license_type:
            clients = clients.filter(license__name__iexact=license_type)
        
        if trading_status:
            clients = clients.filter(is_enable=(trading_status.lower() == 'on'))
        
        # if broker_type:
        #     clients = clients.filter(Broker__name__icontains=broker_type)
        # Apply pagination and serialize the data
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(clients, request)
        serializer = ClientListSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
#Client ADD Api
class ClientCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user 
        if user.role and user.role.name.lower() == 'super-admin' or user.role.name =='Super-Admin':
            clients = User.objects.filter(type_of_user='is_client', is_client=True).order_by('-id')
        # elif user.role and user.role.name.lower() == 'sub-admin' or user.role.name=='Sub-Admin':
            # print("sub-admin.........")
            # clients = User.objects.filter(assigned_client=user).order_by('-id')
        else:
            clients = User.objects.filter(Q(type_of_user='is_client') & (Q(created_by=user) 
            | Q(assigned_client=user))).order_by('-id')
            # clients = User.objects.filter(type_of_user='is_client',is_client=True, created_by=user).order_by('-id')
                # Apply additional filters based on query parameters
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(clients, request)
        serializer = ClientListSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        start_time=time.time()
        print("data>>>>",data)
        serializer = ClientCreateSerializer(data=data)
        password = get_random_string(length=12)
        if serializer.is_valid():
            client = serializer.save(created_by=request.user)
            client.set_password(password)  
            client.external_user=False
            client.save() 
            
                    # Handle segment and subsegment addition
            segment_id = data.get("segment")
            subsegments = data.get("subsegment", [])
            
            if segment_id and subsegments:
                for subsegment_id in subsegments:
                    trade_settings_data = {
                        "client": client.id,
                        "segment": segment_id,
                        "sub_segment": subsegment_id,
                        # Add any other fields required for ClientTradeSetting
                    }
                    trade_setting_serializer = ClientTradeSettingSerializer(data=trade_settings_data)
                    if trade_setting_serializer.is_valid():
                        trade_setting_serializer.save()
                    else:
                        print("Trade Setting Error:", trade_setting_serializer.errors)
        
            end_time = time.time()  # Record the end time
            execution_time = end_time - start_time  # Calculate the total time
            print(f"client create API executed in--------- {execution_time:.4f} seconds") 
            start_time=time.time()
            # Send the password via email
            print("client-password---",password)
            send_email_pass_async.delay(
                    client.email,
                    password,
                    client.firstName,
                    login_link,
                    support_email,
                    help_center_link,
                    company_website,
                    contact_number
                )
            # EmailService.send_password_email(client.email, password,client.firstName,login_link,support_email,help_center_link,company_website,contact_number)
            end_time = time.time()  # Record the end time
            execution_time = end_time - start_time  # Calculate the total time
            print(f"client mail password API executed in {execution_time:.4f} seconds") 
            return Response(ClientListSerializer(client).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        client_id = kwargs.get('pk')
        client = get_object_or_404(User, id=client_id)

        serializer = ClientupdateListSerializer(client, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
                    # Handle segment and subsegment update
            segment_id = request.data.get("segment")
            subsegments = request.data.get("subsegment", [])
            
            if segment_id and subsegments:
                # Clear existing subsegments for this client and segment
                ClientTradeSetting.objects.filter(client=client, segment=segment_id).delete()
                
                # Add the new segment and subsegments
                for subsegment_id in subsegments:
                    trade_settings_data = {
                        "client": client.id,
                        "segment": segment_id,
                        "sub_segment": subsegment_id,
                        # Add any additional fields required
                    }
                    trade_setting_serializer = ClientTradeSettingSerializer(data=trade_settings_data)
                    if trade_setting_serializer.is_valid():
                        trade_setting_serializer.save()
                    else:
                        print("Trade Setting Update Error:", trade_setting_serializer.errors)
            
            return Response(ClientListSerializer(client).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, *args, **kwargs):
        client_id = kwargs.get('pk', None)
        if not client_id:
            return Response({"detail": "client ID is required for deletion."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            broker = User.objects.get(pk=client_id)
            broker.delete()
            return Response({"detail": "client deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Broker.DoesNotExist:
            return Response({"detail": "client_id not found."}, status=status.HTTP_404_NOT_FOUND)
class AssignClientToStrategyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, pk):
        strategy = get_object_or_404(Strategies, pk=pk)
        serializer = StrategyAssignSerializer(strategy, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    # def put(self, request, pk):
    #     strategy = get_object_or_404(Strategies, pk=pk)
        
    #     # Extract the list of client IDs from the request data
    #     client_ids = request.data.get('clients', [])
        
    #     if not isinstance(client_ids, list):
    #         return Response(
    #             {"error": "Invalid format. 'clients' should be a list of client IDs."},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )
        
    #     # Add new clients to the strategy without removing existing ones
    #     strategy.clients.add(*client_ids)

    #     # Return the updated strategy with its clients
    #     serializer = StrategyAssignSerializer(strategy)
    #     return Response(serializer.data, status=status.HTTP_200_OK)
class GetclientbyidPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request, pk, *args, **kwargs): 
        try:
            user = User.objects.get(pk=pk)  
            serializer = ClientListdetailsSerializer(user)  
        except Strategies.DoesNotExist:
            return Response({"detail": "client id not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.data, status=status.HTTP_200_OK)        
class GetStrategyClientView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user 
        try:
            if user.role and user.role.name.lower() == 'super-admin' or user.role.name =='Super-Admin':
                clients = User.objects.filter(type_of_user='is_client', is_client=True).order_by('-id')
            elif user.role and user.role.name.lower() == 'sub-admin' or user.role.name=='Sub-Admin':
                clients = User.objects.filter(assigned_client=user).order_by('-id')
            else:
                clients = User.objects.filter(type_of_user='is_client', created_by=user).order_by('-id')
            serializer = ClientListSerializer(clients, many=True)

        except Strategies.DoesNotExist:
            return Response({"detail": "client id not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.data, status=status.HTTP_200_OK)    
#Client penel setting
class ClientTreadSettingView(APIView):
   
    def get(self, request, pk, *args, **kwargs):
        try:
            # Fetch the client with the specified ID
            client = User.objects.get(pk=pk)
            
            # Access Group_service's json_data directly
            group_service = client.Group_service
            if not group_service:
                return Response({"detail": "Group service not found."}, status=status.HTTP_404_NOT_FOUND)
            
            # Ensure json_data is a list and extract ServiceName values
            json_data = group_service.json_data if isinstance(group_service.json_data, list) else []
            service_names = [service.get("ServiceName") for service in json_data if service.get("ServiceName")]

            return Response({"service_names": service_names}, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({"detail": "Client not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def put(self, request, *args, **kwargs):
        client_id = kwargs.get('pk')
        client = get_object_or_404(User, id=client_id)

        serializer = ClientupdateListSerializer(client, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(ClientListSerializer(client).data, status=status.HTTP_201_CREATED)
#client expiry list
class ClientsDataView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            # Get the current date
            current_date = timezone.now().date()
            print(current_date)
            # Fetch clients whose end_date_client has expired and who are of type 'is_client'
            expiry_client = User.objects.filter(client_expiry_status=True, type_of_user='is_client',is_client=True)
            # Serialize the data
            serializer = ClientListSerializer(expiry_client, many=True)
            return Response({"expiry_client_list": serializer.data}, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({"detail": "Client not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)        



class SubSegmentsView(APIView):
    def post(self, request):
        
        """
        Create a new SubSegment.
        """
        serializer = SubSegmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    # def post(self, request, *args, **kwargs):
    #     data = request.data

    #     print("Data saved to nse_stock_list.csv")

    #     segment = Segment.objects.get(id=data.get("segment_id"))

    #     sub_segment = SubSegment.objects.create(
    #         segment=segment,
    #         name=data["name"],
    #         short_name=data.get("short_name"),
    #         status=data.get("status", True),
    #         token=data.get("token"),
    #         Exchange=data.get("Exchange"),
    #     )
        
    #     return Response({
    #         "id": sub_segment.id,
    #         "name": sub_segment.name,
    #         "segment": sub_segment.segment.name,
    #         "short_name": sub_segment.short_name,
    #         "status": sub_segment.status,
    #         "symbol": get_symbol(sub_segment.name),  # Add symbol here
    #         "token": sub_segment.token,
    #         "exchange": sub_segment.Exchange,
    #     })
    def put(self, request, pk):
        """
        Update an existing SubSegment by ID.
        """
        sub_segment = get_object_or_404(SubSegment, pk=pk)
        serializer = SubSegmentSerializer(sub_segment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Delete a SubSegment by ID.
        """
        sub_segment = get_object_or_404(SubSegment, pk=pk)
        sub_segment.delete()
        return Response({"message": "SubSegment deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    def get(self, request):
        # segment_name = request.query_params.get('segment', None)
        
        # if not segment_name:
        #     return Response({"error": "Segment name is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Filter the segment based on the provided name
        try:
            segment = SubSegment.objects.all()
        except SubSegment.DoesNotExist:
            return Response({"error": "Segment not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # # Get all sub-segments associated with the segment
        # sub_segments = segment.sub_segments.all()  # Assuming `sub_segments` is the related name
        
        # Serialize the sub-segments
        serializer = SubSegmentSerializer(segment, many=True)
        
        return Response({"sub_segments": serializer.data}, status=status.HTTP_200_OK)

class UpdateClientTradeSettingAPIView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    
    queryset = ClientTradeSetting.objects.all()
    serializer_class = ClientTradeSettingSerializer

    def update(self, request, *args, **kwargs):
        # Get the authenticated client from the request
        client = request.user
        
        # Extract segment and sub_segment from the request data
        segment = request.data.get('segment')
        sub_segment = request.data.get('sub_segment')

        if not segment or not sub_segment:
            return Response(
                {"detail": "Both segment and sub_segment must be provided."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to fetch the existing trade setting based on client, segment, and sub_segment
        try:
            trade_setting = ClientTradeSetting.objects.get(client=client, segment=segment, sub_segment=sub_segment)
        except ClientTradeSetting.DoesNotExist:
            return Response({"detail": "TradeSetting not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize and validate the incoming data (allow partial updates)
        serializer = self.get_serializer(trade_setting, data=request.data, partial=True)
        
        if serializer.is_valid():
            expiry_date = request.data.get('expiry_date')
            print("expiry_date>>>",expiry_date)
            if expiry_date:
                # Convert to Asia/Kolkata timezone
                india_tz = pytz_timezone('Asia/Kolkata')
                expiry_date = datetime.fromisoformat(expiry_date)
                expiry_date = make_aware(expiry_date, timezone=india_tz)
                trade_setting.expiry_date = expiry_date

            # Save the updated trade setting
            serializer.save()
            # Log the update in TradeLog
            # TradeLog.objects.create(
            #     client=client,
            #     trade_setting=trade_setting,
            #     symbol=trade_setting.symbol,
            #     is_trade_status =trade_setting.is_tread_status,
            #     trade_date=timezone.now()
            # )
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.utils.timezone import localtime
class GetTradeSettingAPIView(generics.ListAPIView):
    serializer_class = GetclientTradedataSettingSerializer#ClientTradeSettingSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        """
        This method returns the queryset filtered by client, segment, and sub_segment.
        """
        client = self.request.query_params.get('client', None)
        segment = self.request.query_params.get('segment', None)
        sub_segment = self.request.query_params.get('sub_segment', None)
        
        queryset = ClientTradeSetting.objects.all()
        
        # Apply filters if present
        if client:
            queryset = queryset.filter(client=client)
        if segment:
            queryset = queryset.filter(segment=segment)
        if sub_segment:
            queryset = queryset.filter(sub_segment=sub_segment)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        Override the list method to include a response with filtered data.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
class UpdateTradeSettingStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Get the authenticated client
            client = request.user
            
            # Get the 'segment' parameter from the query string
            segment_name = request.query_params.get('segment', None)
            
            # Filter trade settings associated with the client
            client_list = ClientTradeSetting.objects.filter(client=client)
            
            # Filter further by segment if the parameter is provided
            if segment_name:
                client_list = client_list.filter(segment__name__iexact=segment_name)
            
            # Serialize the data
            serializer = ClientSegementsSerializer(client_list, many=True)
            
            return Response(
                {"client_segment_list": serializer.data},
                status=status.HTTP_200_OK
            )
        
        except User.DoesNotExist:
            return Response(
                {"detail": "Client not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    def patch(self, request, *args, **kwargs):
        # Get the authenticated user
        user = request.user
        
        # Extract segment, sub_segment, and is_trade_status from request data
        segment = request.data.get('segment')
        sub_segment = request.data.get('sub_segment')
        is_trade_status = request.data.get('is_trade_status')

        if is_trade_status is None:
            return Response({"detail": "'is_trade_status' field is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(is_trade_status, bool):
            return Response({"detail": "'is_trade_status' must be a boolean value."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Find the trade setting for the client based on segment and sub-segment
        try:
            trade_setting = ClientTradeSetting.objects.get(client=user, segment=segment, sub_segment=sub_segment)
        except ClientTradeSetting.DoesNotExist:
            return Response({"detail": "Trade setting not found."}, status=status.HTTP_404_NOT_FOUND)

        # Update the 'is_status' field
        try:
            # Start transaction in case of complex updates
            with transaction.atomic():
                trade_setting.is_tread_status = is_trade_status
                trade_setting.save()
                # Serialize and return updated data
                                # Create a TradeLog entry to record the update
                TradeLog.objects.create(
                    client=user,
                    trade_setting=trade_setting,
                    symbol=trade_setting.symbol,
                    is_trade_status=is_trade_status,
                    trade_date=timezone.now()
                )
                serializer = ClientTradeSettingSerializer(trade_setting)
                return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateTradeStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        # Get the authenticated user
        user = request.user
        
        # Extract query parameters
        segment_name = request.query_params.get('segment')
        sub_segment_name = request.query_params.get('sub_segment')
        is_trade_status = request.data.get('is_trade_status')

        # Validate query parameters and the required field
        if not segment_name or not sub_segment_name:
            return Response({"detail": "'segment' and 'sub_segment' query parameters are required."}, 
                            status=status.HTTP_400_BAD_REQUEST)
        if is_trade_status is None:
            return Response({"detail": "'is_trade_status' field is required."}, 
                            status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(is_trade_status, bool):
            return Response({"detail": "'is_trade_status' must be a boolean value."}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # Look up the Segment and SubSegment objects by name
        try:
            segment = Segment.objects.get(name__iexact=segment_name)
            sub_segment = SubSegment.objects.get(name__iexact=sub_segment_name)
            # Find the trade setting for the client based on segment and sub-segment
            trade_setting = ClientTradeSetting.objects.get(client=user, segment=segment, sub_segment=sub_segment)
        except Segment.DoesNotExist:
            return Response({"detail": f"Segment with name '{segment_name}' not found."}, 
                            status=status.HTTP_404_NOT_FOUND)
        except SubSegment.DoesNotExist:
            return Response({"detail": f"SubSegment with name '{sub_segment_name}' not found."}, 
                            status=status.HTTP_404_NOT_FOUND)
        except ClientTradeSetting.DoesNotExist:
            return Response({"detail": "Trade setting not found."}, 
                            status=status.HTTP_404_NOT_FOUND)

        # Update the 'is_trade_status' field
        try:
            with transaction.atomic():
                trade_setting.is_tread_status = is_trade_status
                trade_setting.save()
                TradeLog.objects.create(
                    client=user,
                    trade_setting=trade_setting,
                    symbol=trade_setting.symbol,
                    is_trade_status=is_trade_status,
                    trade_date=timezone.now()
                )
                # Serialize and return updated data
                serializer = ClientTradeSettingSerializer(trade_setting)
                return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#Active Inactive clints for specific sub-Admin
class clientActiveInactiveView(APIView):
    # Uncomment this if authentication is required
    # permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, id, *args, **kwargs):
        try:
            user = User.objects.get(id=id, role__name='Sub-Admin')
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        current_date = timezone.now().date()

        try:
            # Retrieve active clients and set client_status to "active"
            active_clients = user.assigned_users.filter(
                type_of_user='is_client', is_client=True, client_status=True)
            
            
            # Prepare list of active clients
            active_clients_list = [
                {
                    "id": client.id,
                    "email": client.email,
                    "client_name": client.fullName,
                    "assigned_client_name": user.fullName,
                    "client_status":True,
                    "client_phone": client.phoneNumber,
                    "start_date_client":client.start_date_client,
                    "end_date_client"  :  client.end_date_client,
                }
                for client in active_clients
            ]
        except Exception as e:
            return Response({"error": "Error fetching active clients", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Retrieve inactive clients and set client_status to "inactive"
            inactive_clients = user.assigned_users.filter(
                type_of_user='is_client', is_client=True,client_status=False
            )
            # inactive_clients.update(
            # Prepare list of inactive clients
            inactive_clients_list = [
                {
                    "id": client.id,
                    "email": client.email,
                    "client_name": client.fullName,
                    "assigned_client_name": user.fullName,
                    "client_status": False,
                    "client_phone": client.phoneNumber,
                    "start_date_client":client.start_date_client,
                    "end_date_client"  :  client.end_date_client,
                }
                for client in inactive_clients
            ]
        except Exception as e:
            return Response({"error": "Error fetching inactive clients", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Combine active and inactive clients into one list
            combined_clients_list = active_clients_list + inactive_clients_list
            
            # Serialize user data with combined clients list
            user_data = UserclientSerializer(user).data
            user_data['active_inactive_clients'] = combined_clients_list
        except Exception as e:
            return Response({"error": "Error serializing user data", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(user_data, status=status.HTTP_200_OK)

# clients which are using the  group service
class ClientsByGroupServiceView(APIView):
    def get(self, request, group_service_id, *args, **kwargs):
        group_service = get_object_or_404(GroupService, id=group_service_id)

        clients = User.objects.filter(Group_service=group_service, is_client=True)
        client_data = [
            {
                "id": client.id,
                "email": client.email,
                "client_name": client.fullName,
                "phone_number": client.phoneNumber,
                "service_name": client.Group_service.group_name if client.Group_service else None,
                "license": client.license.name if client.license else None, 
                "client_status": "active" if client.client_status else "inactive",
                "start_date_client":client.start_date_client,
                "end_date_client"  :  client.end_date_client,
                
            }
            for client in clients
        ]

        return Response({"group_service": group_service.group_name, "clients": client_data}, status=status.HTTP_200_OK)

#all active clients for dashboard
class ActiveClientsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        current_date = timezone.now().date()

        if user.role and user.role.name.lower() == 'super-admin':
            clients = User.objects.filter(
                type_of_user='is_client', is_client=True, client_status=True
            ).order_by('-id')
        else:
            # clients =User.objects.filter(
            #     type_of_user='is_client', is_client=True, end_date_client__gt=current_date,created_by=user
            # ).order_by('-id')
            clients = User.objects.filter(
                Q(type_of_user='is_client') & Q(is_client=True) & Q(client_status=True) &
                (Q(created_by=user) | Q(assigned_client=user))
            ).order_by('-id')
        
        # Apply pagination and serialize the data
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(clients, request)
        serializer = ClientListSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
#all In-active clients for dashboard
class InactiveClientsView(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user
        current_date = timezone.now().date()

        if user.role and user.role.name.lower() == 'super-admin':
            clients = User.objects.filter(
                type_of_user='is_client', is_client=True, client_status=False
            ).order_by('-id')
        else:
            # clients = User.objects.filter(
            #     type_of_user='is_client', is_client=True, end_date_client__lte=current_date,created_by=user
            # ).order_by('-id')
            clients = User.objects.filter(
                Q(type_of_user='is_client') & Q(is_client=True) & Q(client_status=False) &
                (Q(created_by=user) | Q(assigned_client=user))
            ).order_by('-id')
        
        # Apply pagination and serialize the data
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(clients, request)
        serializer = ClientListSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


# expiry clients   
class ExpiryClientsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        current_date = timezone.now().date()

        if user.role and user.role.name.lower() == 'super-admin':
            clients = User.objects.filter(
                type_of_user='is_client', is_client=True, end_date_client__lte=current_date,
            ).order_by('-id')
        else:
            # clients = User.objects.filter(
            #     type_of_user='is_client', is_client=True, end_date_client__lte=current_date,created_by=user
            # ).order_by('-id')
            clients = User.objects.filter(
                Q(type_of_user='is_client') & Q(is_client=True) & Q(end_date_client__lte=current_date) &
                (Q(created_by=user) | Q(assigned_client=user))
            ).order_by('-id')
        
        # Apply pagination and serialize the data
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(clients, request)
        serializer = ClientListSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class GetclientdataView(APIView):
    # permission_classes = [IsAuthenticated]
    def get(self,request, *args, **kwargs): 
        try:
            client_list = ClientTradeSetting.objects.filter(is_tread_status=True)
            print(client_list)
            serializer = ClientTradeSettingSerializer(client_list,many=True)
            # print(serializer)
        
        except Strategies.DoesNotExist:
            return Response({"detail": "client id not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.data, status=status.HTTP_200_OK)  

#order -logs -list
class OrderLogListView(APIView):
    pagination_class = None
    def get(self, request, *args, **kwargs):
        # Fetch all the order logs from the database
        order_logs = SignalOrderLog.objects.all().order_by('-id')
        
        # Serialize the data
        serializer = OrderLogSerializer(order_logs, many=True)
        
        # Return the serialized data as a JSON response
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

# Get Alice-Blue orders  GET_ORDER_BOOK_URL
class GetAliceOrderBook(APIView):
    pagination_class = None
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
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {USER_ID} {sessionID}' 
        }
        try:
 
            response = requests.get(GET_ORDER_BOOK_URL, headers=headers)
            response.raise_for_status()  
            return Response({
                "status": "success",
                "data": response.json()
            }, status=status.HTTP_200_OK)

        except requests.RequestException as req_err:
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
    pagination_class = None
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
            print("response>>>>>>>>>>>",response)
            response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
            trade_history = response.json()
            # Return the successful response data
            return Response({
                "status": "success",
                "data": trade_history
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



# Save the order log to the database
from django.utils import timezone  

def save_webhook_signals_logs(order_type,symbol,price,strategy,json=None):#user,status,failure_reason,json=None):
                                  
    """Save order details and status into the log table."""
    try:
        SignalOrderLog.objects.create(
            signal_time=timezone.now(),  # You can change this to the actual signal time
            order_type=order_type,
            symbol=symbol,
            price=price,
            strategy=strategy,
            # user=user,  # Store the client ID here
            # status=status,
            # failure_reason=failure_reason,
            json_data=json
        )
        
        logger.info(f"signal order log saved ")
    except Exception as e:
        logger.error(f"Failed to save webhook signal order log . Reason: {str(e)}")
        
def round_price(price):
    # Get the last two digits of the price before the decimal
    price=float(price)
    last_two_digits = int(price) % 100
    
    if last_two_digits > 50:
        # Round up to the next hundred
        return int(price) - last_two_digits + 100
    else:
        # Round down to the nearest hundred
        return int(price) - last_two_digits
    
# Transaction type mapping dictionary
transaction_type_dict = {
    "BUY-O": "Open a new BUY CE order",
    "SELL-C": "Close an existing SELL CE order",
    "SELL-C_O": "Close an existing SELL CE and open a new PE order",
    "SELL-O": "Open a new SELL PE order",
    "BUY-C": "Close an existing BUY PE order",
    "BUY-C_O": "Close an existing BUY PE and open a new CE order",
    "SELL-O_C": "Close an existing SELL PE and open a new CE order",
    "BUY-O_C": "Close an existing BUY CE and open a new PE order"
}

def manage_order(transaction_type, buy_sell, Type):
    try:
        if transaction_type == "BUY-O":  # Open a new BUY CE order
            buy_sell = "BUY"
            Type = "CE"
        elif transaction_type == "SELL-C":  # Close CE an existing SELL CE order
            buy_sell = "SELL"
            Type = "CE"
        elif transaction_type == "SELL-O":  # BUY PE Open a new  BUY PE order
            buy_sell = "BUY"
            Type = "PE"
        elif transaction_type == "BUY-C":  # Close PE an existing BUY PE order
            buy_sell = "SELL"
            Type = "PE"
        else:
            print(f"Invalid transaction type: {transaction_type}")
            return None, None  # Return None values if transaction type is invalid
        return buy_sell, Type  # Ensure the correct order of return values
    except Exception as e:
        print(f"Error processing transaction: {e}")
        return None, None  # Return None values in case of an exception
def place_order_broker(
    trade, user, transaction_type, symbol, quantity, strategy, ordertype,
    product_type, price, Lots, trade_order_status, Entry_type, Exit_type, Entry_price,
    Exit_price, webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice, day,month, year, default_price, Type, order_params):   
     
    if trade.broker.lower() == "alice blue":
        trading_symbol_aliceblue = f"{symbol}{day}{month}{year}{Type[0]}{default_price}"
        logger.info("trading_symbol_aliceblue.. %s %s", trading_symbol_aliceblue,symbol)
        trade_symbol=trading_symbol_aliceblue
        # Fetch client broker details
        client_broker = ClientBrokerdetails.objects.filter(client=trade.client, broker_name__broker_name=trade.broker).first()
        if not client_broker:
            order_id=0
            status="Failed"
            res_data="unknown response",
            message= f"No broker details found for client {trade.client} and broker {trade.broker}"
            save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy, Entry_type,Exit_type ,Entry_price,Exit_price,webhook_signal , Exchange, Segment,Index_Symbol,order_params,broker="Angle One")
            logger.error(f"No broker details found for client {trade.client} and broker {trade.broker}")
            response= {"data":{"status": "error", "message":message }}
            return response

        api_skey = client_broker.broker_API_SKEY
        api_uid = client_broker.broker_API_UID
        logger.info(f"Fetched API credentials for {trade.broker}: SKEY={api_skey}, UID={api_uid}")

        logger.info(f"!!!!Placing order for user: {user} Brocker is: {trade.broker} & trading symbol is: {trade.symbol}")
        Entry_price=Entry_price
        Exit_price=Exit_price
        order_response=place_alice_orders(api_skey,api_uid,trade_symbol,transaction_type, symbol, quantity,strategy,ordertype,
        product_type, price,user, Lots,trade_order_status,  Entry_type,Exit_type ,Entry_price,Exit_price,webhook_signal ,Exchange, Segment,Index_Symbol,triggerPrice)
    elif trade.broker.lower() == "angle one":
        print("angle one order :::::::::::::::: ")
        trade_symbol = f"{symbol}{day}{month}{year}{default_price}{Type}" 
        # Fetch client broker details
        client_broker = ClientBrokerdetails.objects.filter(client=trade.client, broker_name__broker_name=trade.broker).first()
        if not client_broker:
            order_id=0
            status="Failed"
            res_data="unknown response",
            message= f"No broker details found for client {trade.client} and broker {trade.broker}"
            response= {"data":{"status": "error", "message":message }}
            save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data, message, strategy,  Entry_type,Exit_type ,webhook_signal , Exchange, Segment,Index_Symbol, order_params,broker="Angle One")
                
            logger.error(f"No broker details found for client {trade.client} and broker {trade.broker}")
            return response # continue

        api_key = client_broker.broker_API_SKEY
        demate_user_name = client_broker.broker_Demate_User_Name
        totp = client_broker.broker_Totp_Authcode
        angle_pass = client_broker.broker_pass

        logger.info(f"Fetched API credentials for {trade.broker}: SKEY={api_key}, USER={demate_user_name}")

        logger.info(f"!!!!Placing order for user: {user} Brocker is: {trade.broker} & trading symbol is: {trade.symbol}")
        print("trade_symbol>>>>>>",trade_symbol)
        tokendata = get_token_details(trade_symbol) 
        if tokendata["status"] == "success":  
            token = tokendata.get("token")
            symbol = tokendata.get("symbol")
            if not token or not symbol:
                logger.error(f"Missing token or symbol for trading symbol: {trade.symbol}")
                response= {"data":{"status": "error", "message": "token symbole not found"}}
                return response# continue
        else:
            order_id=0
            status="Failed"
            res_data="unknown response",
            message= f"trading symbol is not found for this :{trade.symbol}"
            save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data,
                                     message, strategy,  Entry_type,Exit_type, Entry_price,Exit_price,webhook_signal , 
                                     Exchange, Segment,Index_Symbol, order_params,broker="Angle One")
                
            logger.info(f"No token data found for trading symbol: {trade.symbol}")
            response= {"data":{"status": "error", "message": "token symbole not found"}}
            return response
            # continue  # Skip to next user if token data is not found

        # Place order for Angle One
        order_response =place_Angle_order( api_key=api_key,demate_user_name=demate_user_name,totp=totp,angle_pass=angle_pass,
            token=token,symbol=symbol,quantity=quantity,product_type=product_type, 
            transactiontype=transaction_type,price=price,ordertype=ordertype,lot_size=Lots,
            Entry_type=Entry_type, Exit_type=Exit_type,Entry_price=Entry_price, Exit_price=Exit_price,
            webhook_signal=webhook_signal,Exchange=Exchange,Segment=Segment,trade_order_status=trade_order_status,
            Index_Symbol=Index_Symbol , user=user, strategy=strategy)#exch_seg=exch_seg expiry=expiry
            
    return order_response    

def serialize_to_json(data):
    """
    Convert data into a JSON-serializable format.
    If a value is a datetime object, convert it to an ISO 8601 string.
    """
    if isinstance(data, dict):
        return {key: serialize_to_json(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [serialize_to_json(item) for item in data]
    elif isinstance(data, Decimal):
        return float(data)  # Convert Decimal to float
    elif isinstance(data, datetime):
        return data.isoformat()  # Convert datetime to ISO 8601 string
    return data

SESSION_ID = None
SESSION_EXPIRATION = None
# Webhook  trade Alert
class PlaceOrderWebhookView(APIView):
    def post(self, request):
        alert_data = request.data
        # Check if alert_data is None or an empty dictionary
        if not alert_data:
            logger.warning("No alert data received or empty payload.")
            return Response({"status": "error", "message": "No alert data received."}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Received alert: {alert_data}")
        # Extract parameters with defaults
        raw_symbol = request.data.get('text', '').upper()
        # default_price = round(float(alert_data.get('signalprice', 0)))
        signal_price=alert_data.get('signalprice', 0)
        default_price = round_price(signal_price)
        print("Round of price:::::::::::",default_price)
        transaction_type = request.data.get('ordertype', 'BUY-O').upper()
        order_type_mapping = {
            "BUY-O": "Buy CE",
            "SELL-C": "Close CE",
            "SELL-C_O": "Close CE & BUY PE",
            "SELL-O": "BUY PE",
            "BUY-C": "Close PE",
            "BUY-C_O": "Close PE & Buy CE"
        }
        # Get the description and split action/type
        action_description = order_type_mapping.get(transaction_type, "Invalid OrderType")
        if action_description == "Invalid OrderType":
            logger.error(f"Invalid OrderType received: {transaction_type}")
            return Response({"status": "error", "message": "Invalid OrderType received."}, status=status.HTTP_400_BAD_REQUEST)
        # Split type
        action_split = action_description.split()
        transaction_split= transaction_type.split('-')
        buy_sell =action_split[-1]# transaction_split[0]  #  'BUY' or 'SELL'
        # Type = action_split[-1]  # CE or PE
        print("buy_sell>>>>",buy_sell)
        # Map raw symbol to standardized symbol
        symbol_mapping = {
            "NIFTY BANK": "BANKNIFTY",
            "NIFTY 50": "NIFTY",
            "NIFTY FIN SERVICE": "FINNIFTY",
            "MID CAP NIFTY": "MIDCAPNIFTY"
        }
        symbols = symbol_mapping.get(raw_symbol, raw_symbol)  # Default to raw_symbol if no matc
        if symbols.upper()=="SENSEX":
            exch_seg="BSE"
        else:
            exch_seg="NFO" 
        default_ordertype = request.data.get('orderType', 'MARKET')
        strategy=request.data.get('strategyTag',"ce entry")
        limitPrice=request.data.get('limitPrice',0)
        default_quantity=0
        Lots=1
        triggerPrice=0
        # producttype=None
        save_webhook_signals_logs(buy_sell, symbols, default_price, strategy, json=alert_data)
        buy_sell_type=transaction_type
        all_enable_users = ClientTradeSetting.objects.filter(is_tread_status=True,client__is_enable=True, broker__isnull=False)
        user_count = all_enable_users.count()
        print("all_enable_users>>",all_enable_users,">>>count>>>>",user_count)
        default_expiry=None 
        order_status=None        
        try:
            for trade in all_enable_users:
                transaction_type=buy_sell_type
               
                trade_order_status=None
                Entry_price = None
                Exit_price = None
                Entry_type = None
                Exit_type = None
                Type=None
                trade_symbol=symbols 
                user=trade.client
                print("trade for user >>",trade.client)
                if trade.symbol.upper() == symbols:
                    Type=None
                    strategy=trade.strategy
                    Segment=trade.segment.name if trade.segment else None
                    Exchange=exch_seg
                    user=trade.client
                    webhook_signal=alert_data
                    order_id=0
                    status="Failed"
                    Index_Symbol=trade.symbol
                    res_data="unknown response"
                    order_params = {"symbol": trade.symbol,"Exchange": exch_seg, "quantity": trade.quantity or default_quantity,"product_type": trade.product_type,
                    "transaction_type":buy_sell,"price": limitPrice or 0 ,"ordertype": default_ordertype,"strategy": trade.strategy}
                    order_params = serialize_to_json(order_params)
                    if default_expiry:
                        default_expiry=localtime(trade.expiry_date.date())
                        # expiry_date = datetime.strptime(default_expiry, "%d-%m-%Y")
                        expiry_date=default_expiry
                        day = expiry_date.strftime("%d")
                        month = expiry_date.strftime("%b").upper()
                        year = expiry_date.strftime("%y")
                    else:
                        logger.error(f"Expiry date is missing {trade.symbol} for user {trade.client}. Skipping trade.")
                        order_id=0
                        message=f"Expiry date is missing {trade.symbol} for user {trade.client}. so can not get trading symbol"
                        save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy, Entry_type,Exit_type ,Entry_price,Exit_price,webhook_signal , Exchange, Segment,Index_Symbol,order_params,broker=trade.broker)
                        continue 
                    order_params = {"symbol": trade.symbol,"Exchange": exch_seg, "quantity": trade.quantity or default_quantity,"product_type": trade.product_type,
                    "transaction_type":buy_sell,"price": limitPrice or 0 ,"ordertype": default_ordertype, "expiry": default_expiry,"strategy": trade.strategy}
                    order_params = serialize_to_json(order_params)

                    logger.info(f"symbol>>{symbols}>>expiry>{default_expiry} >>Type>>{Type}>>default_price>>{default_price}")
                    # Concatenate fields to create the trading symbol
                    # skip the order and move to next user 
                    broker=trade.broker
                    logger.info(f"Action resolved: EntryType={Entry_type}, EntryPrice={Entry_price}, "
                                f"ExitType={Exit_type}, ExitPrice={Exit_price}")  
                    if  not trade.product_type:
                        message= f"trade details for client {trade.client}: Missing  product type."
                        save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data, message, strategy,  Entry_type,Exit_type ,webhook_signal , Exchange, Segment,Index_Symbol, order_params,broker=trade.broker)      
                        logger.warning(f"Skipping trade for client {trade.client}: Missing  product type")
                        continue
        
                    # Extract user-specific configurations
                    symbol = trade.symbol
                    user = trade.client
                    strategy = trade.strategy
                    quantity = trade.quantity or default_quantity
                    product_type = trade.product_type
                    price = limitPrice
                    ordertype = default_ordertype
                    trade_limit=trade.trade_limit
                    # Count user's trades for the day
                    today = datetime.today()
                    daily_trade_count = TradingLog.objects.filter(client=user, date=today).count()
                    if daily_trade_count >= trade_limit and trade_limit != 0:
                        message= f"Trade limit reached for user {user}. No more trades allowed today."
                        save_trade_order_history(trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type ,Entry_price,Exit_price,webhook_signal , Exchange, Segment,Index_Symbol,order_params,broker=trade.broker)
                        
                        logger.warning(f"Trade limit reached for user {user}. No more trades allowed today.")
                        continue

                    logger.info(f"Placing order for user {user}. Trade count: {daily_trade_count}/{trade_limit}")
                    if is_market_open():
                        print("started place order market is open: transaction_type is :::::::", transaction_type ) 
                        logger.info("Market is open. Proceed with the trade.")
                        if transaction_type=="SELL-C_O":#Will Close the existing order and Open a new PE order
                            # print("SELL-C_O = (Close CE)SELL-C & BUY PE")
                            # First transaction: SELL-C
                            transaction_type = "SELL-C"
                            buy_sell, Type = manage_order(transaction_type, buy_sell, Type)
                            transaction_type=buy_sell
                            logger.info(f"Placing first order: Action={buy_sell}, Type={Type}")
                            trading_Symbol_sum(trade, symbols, day, month, year, Type, default_price)
                            order_response = place_order_broker(
                                trade, user, transaction_type, symbol, quantity, strategy, ordertype,
                                product_type, price, Lots, trade_order_status, Entry_type, Exit_type,
                                Entry_price, Exit_price, webhook_signal, Exchange, Segment, Index_Symbol,
                                triggerPrice, day, month, year, default_price, Type, order_params
                            )
                            # if order_response:
                            print("again one order for SELL-O")
                            # Second transaction: BUY-PE
                            transaction_type = "SELL-O"
                            print("")
                            buy_sell, Type = manage_order(transaction_type, buy_sell, Type)
                            logger.info(f"Placing second order: Action={buy_sell}, Type={Type}")
                            transaction_type=buy_sell
                            order_response = place_order_broker(
                                trade, user, transaction_type, symbol, quantity, strategy, ordertype,
                                product_type, price, Lots, trade_order_status, Entry_type, Exit_type,
                                Entry_price, Exit_price, webhook_signal, Exchange, Segment, Index_Symbol,
                                triggerPrice, day, month, year, default_price, Type, order_params
                            )
                        elif transaction_type=="BUY-C_O":# - Close PE & Buy CE"  BUY-C=PE CLOSE ,BUY-O = Buy CE
                            # First transaction: BUY-C
                            transaction_type = "BUY-C"
                            buy_sell, Type = manage_order(transaction_type, buy_sell, Type)
                            transaction_type=buy_sell
                            logger.info(f"Placing first order: Action={buy_sell}, Type={Type}")
                            order_response = place_order_broker(
                                trade, user, transaction_type, symbol, quantity, strategy, ordertype,
                                product_type, price, Lots, trade_order_status, Entry_type, Exit_type,
                                Entry_price, Exit_price, webhook_signal, Exchange, Segment, Index_Symbol,
                                triggerPrice, day, month, year, default_price, Type, order_params
                            )
                            # if order_response:
                            print("again one order for SELL-O")
                            # Second transaction: BUY-CE
                            transaction_type = "BUY-O"
                            print("")
                            buy_sell, Type = manage_order(transaction_type, buy_sell, Type)
                            logger.info(f"Placing second order: Action={buy_sell}, Type={Type}")
                            transaction_type=buy_sell
                            order_response = place_order_broker(
                                trade, user, transaction_type, symbol, quantity, strategy, ordertype,
                                product_type, price, Lots, trade_order_status, Entry_type, Exit_type,
                                Entry_price, Exit_price, webhook_signal, Exchange, Segment, Index_Symbol,
                                triggerPrice, day, month, year, default_price, Type, order_params
                            )
                        else:
                            print("signal trasaction type................",transaction_type)
                            buy_sell, Type = manage_order(transaction_type, buy_sell, Type)
                            print(f"Action: {buy_sell}, Type: {Type}")
                            transaction_type=buy_sell
                            order_response=place_order_broker(trade,user,transaction_type, symbol, quantity,strategy,ordertype,
                            product_type, price, Lots,trade_order_status,  Entry_type,Exit_type ,Entry_price,Exit_price,
                            webhook_signal ,Exchange, Segment,Index_Symbol,triggerPrice,day,month,year,default_price,Type,order_params)
                              
                        # Check order response and log or handle failures
                        print("final order repsone :::::::::::::::::::::",order_response)
                        if order_response['data']['status'] == "Unauthorized":
                            order_status = f"Unauthorized Order placement failed for {trade.symbol} with broker {trade.broker}"
                            logger.warning(order_status)  # Log the unauthorized order status
                            continue  # Skip to the next client trade if unauthorized
                        elif order_response['data']['status'] =="complete":
                            order_status=f"Order placed successfully for {trade.symbol} with broker {trade.broker}"
                            TradingLog.objects.create(client=user, date=today, symbol=trade.symbol, strategy=strategy,)
                            logger.info(f"Order placed successfully for {trade.symbol} with broker {trade.broker}")
                        elif order_response['data']['status']=="open":   
                            order_status=f"Order is place pending for {trade.symbol} with broker {trade.broker}"
                            logger.error(f"Order place is pending for {trade.symbol} with broker {trade.broker}") 
                        elif order_response['data']['status']=="rejected":
                            order_status=f"Order is rejected for {trade.symbol} with broker {trade.broker}"
                            logger.error(f"Order is rejected for {trade.symbol} with broker {trade.broker}")
                        elif order_response['data']['status']=="error":
                            order_status=f"Error Order placement failed for {trade.symbol} with broker {trade.broker}"
                        else:
                            order_status=f"Order placement failed for {trade.symbol} with broker {trade.broker}"
                    else:
                        logger.info("Market is closed. Do not proceed with the trade.") 
                        order_status=f" can not Trade Order becouse the Market is closed. Do not proceed with the trade"                  
                else:
                    order_status=f"Skipping trade for symbol {trade.symbol} as it doesn't match the specified symbol and transaction type."
                    print(f"Skipping trade for symbol {trade.symbol} as it doesn't match the specified symbol and buy_sell.")
                    continue  # Skip to the next trade if the symbol and buy_sell don't match
                    
                # return Response({"status": order_status})#, status=status.HTTP_200_OK)
                # Return success response after all iterations (if no exceptions are raised)
            return Response({"status":order_status}, status=200)

        except Exception as e:
            logger.error(f"Order placement encountered an error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#token Sesiion id for alice blue order
from datetime import datetime, timedelta
def get_or_regenerate_session_id(USER_ID, ALICE_API_KEY):
    global SESSION_ID, SESSION_EXPIRATION
    current_time = datetime.now()
    if SESSION_ID is None or SESSION_EXPIRATION is None or current_time >= SESSION_EXPIRATION:
        logger.info(f"Session ID expired or not found. Regenerating...{USER_ID}")
        alice = Aliceblue(user_id=USER_ID, api_key=ALICE_API_KEY)
        SESSION_ID = alice.get_session_id(alice)
        SESSION_EXPIRATION = current_time + timedelta(seconds=86400)
        logger.info(f"New session ID generated:")
    else:
        logger.info("Using existing session ID")
    return SESSION_ID



# Get the strategy using the strategy_id
class StrategyClientListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, strategy_id, *args, **kwargs):
        try:
            strategy = get_object_or_404(Strategies, id=strategy_id)
            clients = User.objects.filter(is_client=True)
            if not clients.exists():
                return Response({
                    "strategy_id": strategy.id,
                    "strategy_name": strategy.name,
                    "clients": []
                }, status=200)

            # Build the client data list
            client_data = [
                {
                    "client_id": client.id,
                    "client_name": f"{client.firstName} {client.lastName}",
                    "is_using_strategy": strategy.clients.filter(id=client.id).exists(),
                }
                for client in clients
            ]
            return Response({
                "strategy_id": strategy.id,
                "strategy_name": strategy.name,
                "clients": client_data,
            }, status=200)
        
        except NotFound:
            return Response({"error": "Strategy not found"}, status=404)

        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=500)


class ClientDashboardIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request, *args, **kwargs): 
        try:
            user=request.user
            user = User.objects.get(pk=user.id)  
            serializer = ClientListdetailsSerializer(user)  
        except Strategies.DoesNotExist:
            return Response({"detail": "client id not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.data, status=status.HTTP_200_OK)        
class ClientsTradeStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        current_date = timezone.now().date()

        if user.role and user.role.name.lower() == 'super-admin':
            clients = User.objects.filter(
                type_of_user='is_client', is_client=True).order_by('-id')
        else:
            # clients =User.objects.filter(
            #     type_of_user='is_client', is_client=True, end_date_client__gt=current_date,created_by=user
            # ).order_by('-id')
            clients = User.objects.filter(
                Q(type_of_user='is_client') & Q(is_client=True) &
                (Q(created_by=user) | Q(assigned_client=user))
            ).order_by('-id')
        
        # Apply pagination and serialize the data
        paginator = CustomPageNumberPagination()
        result_page = paginator.paginate_queryset(clients, request)
        serializer = UserclientSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def patch(self, request, *args, **kwargs):
        client_id = kwargs.get('client_id')  # Get client ID from URL
        user = request.user

        # Fetch the client object
        client = get_object_or_404(User, id=client_id, type_of_user='is_client', is_client=True)

        # Check if the current user has the right permissions
        if not (user.role and user.role.name.lower() == 'super-admin') and client.created_by != user:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        # Validate the 'is_enable' field in the request body
        is_enable = request.data.get('is_enable')
        if is_enable is None:
            return Response({"detail": "'is_enable' key is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Update the client's trading status
        client.is_enable = is_enable
        client.save()

        # Serialize the updated client
        serializer = UserclientSerializer(client)
        return Response({"detail": "Trading status updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)



#update client demate account details api
class ClientBrokerDetailsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        """
        Retrieve broker details for the authenticated client.
        """
        try:
            user = request.user
            broker_detail = ClientBrokerdetails.objects.filter(client_id=user.id).first()

            if not broker_detail:
                return Response(
                    {"error": "Broker details not found for the client."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = ClientBrokerDetailsSerializer(broker_detail)
            return Response(
                {"data": serializer.data},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request):

        """
        Create or update broker details for a specific client.
        Resets fields not provided in the request to null.
        """
        try:
            user = request.user

            # Fetch or create broker details for the client
            broker_detail, created = ClientBrokerdetails.objects.get_or_create(client_id=user.id)

            # List of all fields in the model
            all_fields = [field.name for field in ClientBrokerdetails._meta.get_fields()]

            # Loop through all fields and set them to null if they are not in the request data
            for field in all_fields:
                if field != 'id' and field != 'client' and field != 'broker_name':  # Exclude non-updatable fields (like 'id', 'client', 'broker_name')
                    if field not in request.data:
                        setattr(broker_detail, field, None)

            # Use the serializer with partial=True to update only provided fields
            serializer = ClientBrokerDetailsUpdateSerializer(broker_detail, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                message = "Broker details created successfully!" if created else "Broker details updated successfully!"
                return Response({"message": message, "data": serializer.data}, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


#demate status manage api for client trade
class EnableDisableBrokerView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request):
        """
        Enable or disable broker for a specific client.
        """
        # Fetch the client (User)
        try:
            user=request.user
            client = User.objects.get(id=user.id)
        except User.DoesNotExist:
            return Response({"error": "Client not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure 'is_enable' is provided in the request data
        is_enable = request.data.get("is_enable")
        if is_enable is None:
            return Response({"error": "Missing 'is_enable' field in request."}, status=status.HTTP_400_BAD_REQUEST)

        # Update the 'is_enable' field
        client.is_enable = is_enable
        client.save()

        status_message = "enabled" if is_enable else "disabled"
        return Response(
            {"message": f"Broker has been {status_message} for the client."},
            status=status.HTTP_200_OK
        )
    
    def get(self, request):
        """
        Fetch broker status for the authenticated client.
        """
        try:
            user = request.user
            client = User.objects.get(id=user.id)
        except User.DoesNotExist:
            return Response({"error": "Client not found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch and return the broker's status
        return Response(
            {
                "id": client.id,
                "username": client.fullName,
                "email": client.email,
                "is_enable": client.is_enable,  # Assuming this field exists in the User model
            },
            status=status.HTTP_200_OK
        )
        
class SubSegmentsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Get the 'segment' parameter from the query string
            segment_id = request.query_params.get('segment', None)

            # Check if the segment_id is provided
            if not segment_id:
                return Response(
                    {"detail": "Segment ID is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the Segment object
            option_segment = Segment.objects.get(id=segment_id)

            # Retrieve all related sub-segments
            related_sub_segments = option_segment.sub_segments.all()

            # Serialize the related sub-segments
            serializer = SubSegmentSerializer(related_sub_segments, many=True)
            return Response(
                {"client_segment_list": serializer.data},
                status=status.HTTP_200_OK
            )

        except Segment.DoesNotExist:
            return Response(
                {"detail": "Segment not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
#trading history api demate rejected and success status
class TradeorderhistoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            if user.role and user.role.name.lower() == 'super-admin':
                # Super-admin can see all clients' trade order histories
                clients = User.objects.filter(type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.exclude(order_id=0).filter(client__in=clients).order_by('-id')
            elif user.role and user.role.name.lower() == 'sub-admin':
                # Sub-admin can see trade order histories of their assigned clients
                clients = User.objects.filter(assigned_client=user,created_by=user,type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.exclude(order_id=0).filter(client__in=clients).order_by('-id')
            else:
                trade_history = Tradeorderhistory.objects.exclude(order_id=0).filter(client=user).order_by('-id')

            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(trade_history, request)

            serializer = TradeorderhistorySerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#CLIENT trade all history data 
class ClientTradeListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            if user.role and user.role.name.lower() == 'super-admin':
                # Super-admin can see all clients' trade order histories
                clients = User.objects.all()#filter(type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.filter(client__in=clients).order_by('-id')
            elif user.role and user.role.name.lower() == 'sub-admin':
                print("Sub-AdminSub-AdminSub-AdminSub-Admin")
                # Sub-admin can see trade order histories of their assigned clients
                clients = User.objects.filter(assigned_client=user,created_by=user)#,type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.filter(client__in=clients).order_by('-id')
            else:
                trade_history = Tradeorderhistory.objects.filter(client=user).order_by('-id')

            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(trade_history, request)

            serializer = TradeorderhistorySerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClientDashBoardView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ClientdashboardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    
#auth callback url demate---------------------------
from django.http import JsonResponse
from django.shortcuts import redirect
from datetime import timedelta
from django.utils.timezone import now
from .models import ClientBrokerdetails
from kiteconnect import KiteConnect  # For Zerodha
# Import other broker-specific SDKs as needed
    
#ZERODHA...............
def zerodha_callback1(request):
    # Extract the request_token and state from the query parameters
    request_token = request.GET.get('request_token')
    state = request.GET.get('state')

    # Extract user ID from the state
    user_id = state.split('-')[1] if state and '-' in state else None

    try:
        if not request_token or not user_id:
            return JsonResponse({"error": "Invalid request. Missing parameters."}, status=400)
        # Retrieve the broker details for the user
        broker_details = ClientBrokerdetails.objects.get(client_id=user_id)
        # Initialize the KiteConnect instance
        kite = KiteConnect(api_key=broker_details.broker_API_UID)

        # Generate the access token
        session_data = kite.generate_session(request_token, api_secret=broker_details.broker_API_SKEY)
        access_token = session_data['access_token']

        # Save tokens in the database
        broker_details.request_token = request_token
        broker_details.access_token = access_token
        broker_details.access_token_expiry = now() + timedelta(days=1)  # Assuming 1-day token validity
        broker_details.save()

        return JsonResponse({
            "message": "Callback successful",
            "access_token": access_token,
            "state": state,
        })

    except ClientBrokerdetails.DoesNotExist:
        return JsonResponse({"error": "Broker details not found for the user"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
#place order using zerodha api 

def place_zerodha_order(request):
    # user = request.user

    # Ensure user is authenticated
    # if not user.is_authenticated:
    #     return JsonResponse({"error": "User not authenticated"}, status=403)
    api_key = "jsdgh8p7k3yvfii8"
    api_secret = "f6hk1ihfqsc05j22mzjxi5z74zh4qh6h"
    # Retrieve broker details for the user
    try:
        # broker_details = ClientBrokerdetails.objects.get(client=user, broker_name__broker_name="ZERODHA")
        kite = KiteConnect(api_key=api_key)
        # # Check if access token is valid
        # if not broker_details.access_token or broker_details.access_token_expiry < datetime.now():
        #     return JsonResponse({"error": "Access token is missing or expired. Please reauthenticate."}, status=401)
        token="fk9XE0LyQK5xgNk2353gJXNozlgP1IHb"
        # Initialize KiteConnect with API key and access token
        # kite = KiteConnect(api_key=broker_details.broker_API_UID)
        kite.set_access_token(token)
        exchange="NFO"
        symbol="NIFTY25JAN24850CE"
        trading_symbol = get_trading_symbol(exchange, symbol,kite)
        # Order details
        order_params = {
            "tradingsymbol": trading_symbol,
            "exchange": "NFO",
            "transaction_type": "BUY",
            "quantity": 25,
            "order_type": "MARKET",
            "product": "NRML",
        }

        # Place order
        try:
            order_response = kite.place_order(variety=kite.VARIETY_REGULAR, **order_params)
            order_id=order_response
            order_history_response = get_order_details(order_id, token)
            return JsonResponse({"message": "Order placed successfully", "order_response": order_response})
        except Exception as e:
            return JsonResponse({"error": f"Failed to place order: {str(e)}"}, status=500)

        return JsonResponse({"error": "Broker details not found for the user"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
import csv
from kiteconnect import KiteConnect
from kiteconnect import KiteConnect
from django.http import JsonResponse

def get_order_details(order_id, access_token):
    """
    Retrieve order history for a given order ID from Zerodha Kite Connect.
    """
    api_key = "jsdgh8p7k3yvfii8"  # Replace with your API key
    try:
        # Initialize KiteConnect
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        
        # Fetch order history
        try:
            order_history = kite.order_history(order_id)
            return JsonResponse({"order_history": order_history}, status=200)
        except Exception as e:
            return JsonResponse({"error": f"Failed to fetch order history: {str(e)}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Failed to initialize KiteConnect: {str(e)}"}, status=500)

def get_trading_symbol(exchange, symbol, kite):
    try:
        # Fetch the list of instruments for the specified exchange
        instruments = kite.instruments(exchange)
        # csv_file = "/home/digiprima/Desktop/jyoti/Django/AlgoView-Devlopment/Backend/zerodhaNFO.csv"

        # # Write data to a CSV file
        # with open(csv_file, mode='w', newline='') as file:
        #     print("))))))))")
        #     writer = csv.writer(file)
        #     writer.writerow(['Token', 'Trading Symbol', 'Name', 'Exchange Segment', 'Expiry', 'Instrument Type'])
        #     print("LLLLLLLLLLLLLLLLLL")
        #     for entry in instruments:
        #         print("entry>>>>>>",entry)
        #         if entry.get('exchange') == 'NFO':  # Check if the segment is NFO
        #             print("nfooooooooo")
        #             writer.writerow([
        #                 entry.get('instrument_token', ''),
        #                 entry.get('tradingsymbol', ''),
        #                 entry.get('name', ''),
        #                 entry.get('segment', ''),
        #                 entry.get('expiry', ''),
        #                 entry.get('instrument_type', ''),
        #             ])
        #         else:
        #             pass
                    # print("elseeeeeeeee")
        # Find the instrument by the symbol
        for instrument in instruments:
            if instrument['tradingsymbol'] == symbol:
                print("Trading Symbol Found:", instrument['tradingsymbol'])
                return instrument['tradingsymbol']
        
        return None  # Return None if the symbol is not found

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

#










def generate_checksum(api_key, api_secret, request_token):
    import hashlib
    return hashlib.sha256(f"{api_key}{request_token}{api_secret}".encode()).hexdigest()
from django.shortcuts import redirect

def login_zerodha_redirect(request):
    # user=request.user
    # broker_details = ClientBrokerdetails.objects.filter(client=user)
    # api_key=broker_details.broker_API_UID
    # Zerodha API credentials
    api_key = "jsdgh8p7k3yvfii8"  # Replace with your API Key
    redirect_url ="https://software.algosparks.co.in/#/login"# "http://127.0.0.1:8000/callback-zerodha/"  # Your callback URL
    state = "example_state"  # Optional, to track the request state

    # Construct the URL
    zerodha_url = (
        f"https://kite.zerodha.com/connect/login?api_key={api_key}&v=3"
        f"&state={state}"
    )
    print("zerodha_url777",zerodha_url)
    return redirect(zerodha_url)

from django.http import JsonResponse
import requests

def zerodha_callback(request):
    # Extract the request_token and state from query parameters
    request_token = "nnP5J4xXUFglLI3WrlYseIlgpchQRQZM"#request.GET.get('request_token')
    state = "success"#request.GET.get('state')

    if not request_token:
        return JsonResponse({"error": "Request token not provided"}, status=400)

    # Fetch the access token using the request token
    api_key = "jsdgh8p7k3yvfii8"
    api_secret = "f6hk1ihfqsc05j22mzjxi5z74zh4qh6h"

    try:
        AUTH_TOKEN_URL="https://api.kite.trade/session/token"
        headers={
                "api_key": api_key,
                "request_token": request_token,
                "checksum": generate_checksum(api_key, api_secret, request_token),
            }
        # Make a POST request to fetch the access token
        response = requests.post(AUTH_TOKEN_URL,headers)
        response_data = response.json()
        print("response_data>>>",response_data)
        return JsonResponse({
            "message": "Callback successful",
            "access_token": response_data.get("access_token"),
            "state": state,
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def generate_checksum(api_key, api_secret, request_token):
    import hashlib
    return hashlib.sha256(f"{api_key}{request_token}{api_secret}".encode()).hexdigest()
#5 Paisa -----------------

def oauth_callback(request):
    # Extract the request token and state from the callback URL parameters
    request_token = request.GET.get('RequestToken')
    state = request.GET.get('state')

    if not request_token:
        return JsonResponse({"error": "RequestToken not provided"}, status=400)

    # Handle the token (e.g., save it, or use it to fetch an access token)
    return JsonResponse({
        "message": "Callback successful",
        "request_token": request_token,
        "state": state,
    })
from django.shortcuts import redirect 
    
def login_redirect(request):
    vendor_key = settings.VENDOR_KEY
    response_url = settings.RESPONSE_URL
    state = "test_state"  # Optional, for tracking requests
    
    redirect_url = f"https://dev-openapi.5paisa.com/WebVendorLogin/VLogin/Index?VendorKey={vendor_key}&ResponseURL={response_url}&State={state}"
    return redirect(redirect_url)



from django.shortcuts import redirect

def login_angelone_redirect(request):
    # Angel One API credentials
    api_key = "DHKO4GA8"  # Replace with your API Key
    redirect_url = "https://staging.cricratings.com/user/"  # "http://127.0.0.1:8000/callback-angelone/"#
    state = "example_state"  # Optional, to track request state

    # Construct the Angel One login URL 
    angelone_url = (
        f"https://smartapi.angelbroking.com/publisher-login"
        f"?api_key={api_key}&redirect_url={redirect_url}&state={state}"
    )
    return redirect(angelone_url)

from django.http import JsonResponse
import requests
# API_KEY = 'StvD7EVL'  
# USERNAME = 'AAAB519761'  
# PASSWORD = '1234' 
# TOTP_SECRET = "RFFORAS7ASFH7KIZWD7FCSVK2Y" from django.http import JsonResponse
import requests
import pyotp

def angelone_callbackaa(request):
    # Extract the authorization code from the query parameters
    auth_code = request.GET.get('code')

    if not auth_code:
        return JsonResponse({"error": "Authorization code not provided"}, status=400)
# AAAB519761
    # Angel One credentials
    api_key = "DHKO4GA8"
    username = "Algo123"
    password = "1234"
    totp_secret = "RFFORAS7ASFH7KIZWD7FCSVK2Y"

    # Generate TOTP
    totp = pyotp.TOTP(totp_secret).now()

    # Exchange authorization code for access token
    try:
        response = requests.post(
            "https://smartapi.angelbroking.com/rest/auth/login",
            json={
                "api_key": api_key,
                "client_code": username,
                "password": password,
                "totp": totp,
            },
        )
        response_data = response.json()

        if response.status_code == 200:
            return JsonResponse({
                "message": "Callback successful",
                "access_token": response_data.get("data", {}).get("jwtToken"),
                "refresh_token": response_data.get("data", {}).get("refreshToken"),
            })
        else:
            return JsonResponse({"error": response_data.get("message")}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
import pyotp
totp_secret = "RFFORAS7ASFH7KIZWD7FCSVK2Y"
totp = pyotp.TOTP(totp_secret).now()
# print(f"TOTP: {totp}")
from django.http import JsonResponse
import requests

def angelone_callback(request):
    # Extract the authorization code and state from the query parameters
    auth_code = request.GET.get('auth_code')
    print(">>>>>>>>>>>>",auth_code)
    state = request.GET.get('state')
    
    if not auth_code:
        return JsonResponse({"error": "Authorization code not provided"}, status=400)

    # Fetch the access token using the authorization code
    api_key = "DHKO4GA8"
    client_code = "Algo123"  # Replace with your Angel One client code
    secret_key = "f85d6a33-b86d-4864-98a5-f61062b7545b"  # Replace with your Angel One secret key

    try:
        # Make a POST request to fetch the access token
        response = requests.post(
            "https://smartapi.angelbroking.com/rest/authentication/v1/login",
            json={
                "api_key": api_key,
                "clientcode": client_code,
                "authcode": auth_code,
                "secretkey": secret_key,
            },
        )
        response_data = response.json()
        return JsonResponse({
            "message": "Callback successful",
            "access_token": response_data.get("data", {}).get("jwtToken"),
            "refresh_token": response_data.get("data", {}).get("refreshToken"),
            "state": state,
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
from django.http import HttpResponseRedirect
from django.http import HttpResponseRedirect

def login_aliceblue(request):
    APP_CODE = "pyZPOPZiZzCMaWQ"  # Your app code
    CALLBACK_URL = "https://software.alcrafttechnology.com/backend/AliceBlue"  # Your callback URL after successful login
    
    # Build the login URL with app code and callback URL
    LOGIN_URL = f"https://ant.aliceblueonline.com/?appcode={APP_CODE}"#&redirect_uri={CALLBACK_URL}"  # Include the callback URL
    
    # Redirect the user to Alice Blue login page
    return HttpResponseRedirect(LOGIN_URL)


# def login_aliceblue(request):
#     App_Code = "pyZPOPZiZzCMaWQ"  # Replace with your Alice Blue API key
#     CALLBACK_URL = "http://127.0.0.1:8000/callback/aliceblue/"  # Your callback URL
#     LOGIN_URL = f"https://ant.aliceblueonline.com/oauth2/auth?response_type=code&client_id={API_KEY}&redirect_uri={CALLBACK_URL}"
  
#     # Redirect to Alice Blue login page
#     return HttpResponseRedirect(LOGIN_URL)import requests
from django.http import JsonResponse

def aliceblue_callback(request):
    auth_code = request.GET.get("code")  # Extract the authorization code
    if not auth_code:
        return JsonResponse({"error": "auth_code is missing"}, status=400)

    access_token = fetch_aliceblue_access_token(auth_code)
    if access_token:
        return JsonResponse({"access_token": access_token})
    else:
        return JsonResponse({"error": "Failed to fetch access token"}, status=500)

def fetch_aliceblue_access_token(auth_code):
    userId = 857984
    ALICE_API_KEY ="hFSWodPXI0yJXnXcYBZnfFLqJM0YQm6t9mvn5WmtQrkcvXFcZRpq8tK3BKueJQDI4vSOHVYUzi2kLiKdWCnsO0SyfsSMsGFL3US3fikNU8cFGVXVXH8682zjvK7qLulP"

    # SECRET_KEY = "your_secret_key"  # Replace with your Alice Blue API secret key
    CALLBACK_URL = "http://127.0.0.1:8000/callback/aliceblue/"  # Your callback URL
    
    TOKEN_URL = "https://ant.aliceblueonline.com/oauth2/token"
    
    payload = {
        "userId": userId,
        "ALICE_API_KEY":ALICE_API_KEY,
        "userData": auth_code
     } 
    
    response = requests.post(TOKEN_URL, data=payload)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")  # Return access token
    return None


from django.shortcuts import redirect
from django.http import JsonResponse
from kiteconnect import KiteConnect
from django.contrib.auth.decorators import login_required
from .models import ClientBrokerdetails
REDIRECT_URI = "http://127.0.0.1:8000/auth-callback/"  
class BrokerLoginRedirectView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request, *args, **kwargs):
        print("broker login api is called...................")
        user = request.user  
        if not user.is_authenticated:
            return Response({"error": "User not authenticated"}, status=403)

        try:
            # Retrieve broker details for the logged-in user
            broker_details = ClientBrokerdetails.objects.get(client=user)
            broker_name = broker_details.broker_name.broker_name.lower()

            if broker_name == "zerodha":
                return self.redirect_to_zerodha(broker_details)

            elif broker_name == "5paisa":
                return self.redirect_to_5paisa(broker_details)

            elif broker_name == "alice blue":
                return self.redirect_to_alice_blue(broker_details)

            elif broker_name == "upstox":
                return self.redirect_to_upstox(broker_details)

            else:
                return Response({"error": "Unsupported broker"}, status=400)

        except ClientBrokerdetails.DoesNotExist:
            return Response({"error": "Broker details not found for the user"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def redirect_to_zerodha(self, broker_details):
        api_key = broker_details.broker_API_UID
        # redirect_url = "http://127.0.0.1:8000/auth-callback/"  #
        redirect_url ="https://software.algosparks.co.in/#/login"# Replace with your callback URL
        state = f"user-{broker_details.client.id}"  # Include user-specific state
        zerodha_url = (
            f"https://kite.zerodha.com/connect/login?api_key={api_key}&v=3"
            f"&redirect_uri={redirect_url}&state={state}"
        )
        return redirect(zerodha_url)

    def redirect_to_5paisa(self, broker_details):
        vendor_key = settings.VENDOR_KEY
        response_url = settings.RESPONSE_URL
        state = "test_state"  # Optional, for tracking requests
        
        paisa_url = f"https://dev-openapi.5paisa.com/WebVendorLogin/VLogin/Index? VendorKey={vendor_key}&ResponseURL={response_url}&State={state}"
        return redirect(paisa_url)

    def redirect_to_alice_blue(self, broker_details):
        return redirect("login-aliceblue")  

    def redirect_to_upstox(self, broker_details):
        CLIENT_KEY = broker_details.broker_API_UID
        print("CLIENT_KEY>>>",CLIENT_KEY)
        CLIENT_SECRET = broker_details.broker_API_SKEY
        AUTH_URL = "https://api.upstox.com/v2/login/authorization/dialog"
        # Construct the login URL
        REDIRECT_URI= 'https://software.alcrafttechnology.com/login' 
        login_url = (
            f"{AUTH_URL}?client_id={CLIENT_KEY}&response_type=Auth_code"
            # f"redirect_uri={REDIRECT_URI}&"
            f"response_type=Auth_code"
        )
        print("login_url>>",login_url)
        return Response({"redirect_url": login_url})
        # return redirect(login_url)

class BrokerCallbackView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request, *args, **kwargs):
        print("callback url calleddd......")
        # Get the authorization code and state from the URL
        request_token = "YeiOQP"#request.GET.get('Auth_code')
        if not request_token:
            raise ValidationError("Authorization code missing")
        try:
            user = request.user  
            broker_details = ClientBrokerdetails.objects.get(client=user)
            print("broker_details:::::::::::",broker_details)
            broker_name = broker_details.broker_name.broker_name.lower()

            # Handle different brokers
            if broker_name == "zerodha":
                return self.handle_zerodha(request_token, broker_details)

            elif broker_name == "5paisa":
                return self.handle_5paisa(request_token, broker_details)

            elif broker_name == "alice blue":
                return self.handle_alice_blue(request_token, broker_details)

            elif broker_name == "upstox":
                return self.handle_upstox(request_token, broker_details)

            else:
                raise ValidationError("Unsupported broker")

        except ClientBrokerdetails.DoesNotExist:
            raise ValidationError("Broker details not found for the user")
        except Exception as e:
            raise ValidationError(str(e))

    def handle_zerodha(self, request_token, broker_details):
        try:
            kite = KiteConnect(api_key=broker_details.broker_API_UID)
            session_data = kite.generate_session(request_token, api_secret=broker_details.broker_API_SKEY)
            access_token = session_data['access_token']
            
            # Save access token and other details
            broker_details.request_token = request_token
            broker_details.access_token = access_token
            broker_details.access_token_expiry = now() + timedelta(days=1)  # Assuming 1-day validity
            broker_details.save()
            
            return JsonResponse({"message": "Zerodha callback processed successfully", "access_token": access_token})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
            # try:
            #     AUTH_TOKEN_URL="https://api.kite.trade/session/token"
            #     headers={
            #             "api_key": broker_details.broker_API_SKEY,
            #             "request_token": request_token,
            #             "checksum": generate_checksum(broker_details.broker_API_SKEY, broker_details.broker_API_UID, request_token),
            #         }
            #     # Make a POST request to fetch the access token
            #     response = requests.post(AUTH_TOKEN_URL,headers)
            #     response_data = response.json()
            #     print("response_data>>>",response_data)
            #     return JsonResponse({
            #         "message": "Callback successful",
            #         "access_token": response_data.get("access_token"),
                    
            #     })
            # except Exception as e:
            #     return JsonResponse({"error": str(e)}, status=500)
    def handle_5paisa(self, request_token, broker_details):
        try:
            access_token = "5paisa_access_token_placeholder"
            broker_details.request_token = request_token
            broker_details.access_token = access_token
            broker_details.access_token_expiry = now() + timedelta(days=1) 
            broker_details.save()
            
            return JsonResponse({"message": "5Paisa callback processed successfully", "access_token": access_token})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def handle_alice_blue(self, request_token, broker_details):
        try: 
            access_token = "aliceblue_access_token_placeholder" 
            
            # Save access token and other details
            broker_details.request_token = request_token
            broker_details.access_token = access_token
            broker_details.access_token_expiry = now() + timedelta(days=1)  # Assuming 1-day validity
            broker_details.save()
            
            return JsonResponse({"message": "Alice Blue callback processed successfully", "access_token": access_token})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def handle_upstox(self, request_token, broker_details):
        try:
            # Example Upstox-specific token generation logic
            TOKEN_URL = 'https://api.upstox.com/v2/login/authorization/token' 
            auth_code = request_token  # Assuming `request_token` is the auth code
            
            if not auth_code:
                return JsonResponse({"error": "Authorization code not provided"}, status=400)
            data = {
                'code': auth_code,
                'client_id': broker_details.broker_API_UID,
                'client_secret': broker_details.broker_API_SKEY,
                'redirect_uri':REDIRECT_URI,
                'grant_type': 'authorization_code'
            }
            
            response = requests.post(TOKEN_URL, data=data)
            
            if response.status_code == 200:
                access_token = response.json().get('access_token')
                
                # Save access token and other details
                broker_details.request_token = request_token
                broker_details.access_token = access_token
                broker_details.access_token_expiry = now() + timedelta(days=1)  # Assuming 1-day validity
                broker_details.save()
                
                return JsonResponse({"message": "Upstox callback processed successfully", "access_token": access_token})
            else:
                return JsonResponse({"error": "Failed to get access token from Upstox"}, status=400)
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
