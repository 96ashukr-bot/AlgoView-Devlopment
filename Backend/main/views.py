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
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
import time
from datetime import date, datetime as dtmod
from rest_framework.generics import ListAPIView,UpdateAPIView
from main.angleapi import exit_existing_buy_position_angleone, get_token_details, place_Angle_order
from main.dematemodule import  exit_existing_buy_position_5PaisaOrder, exit_existing_buy_position_Aliceblue, exit_existing_buy_position_DhanOrder, exit_existing_buy_position_Upstox, exit_existing_buy_position_fyers_order, exit_existing_buy_position_zerodha_order, trading_Symbol_sum
from main.dhanapi import place_dhan_orders
from main.fivepaisa import fetch_access_token_5paisa, place_5paisa_order
from main.fyersapi import place_fyers_orders
from main.permissions import  IsAdminRole
from main.tasks import resend_otp_email_async, send_kyc_email_async, send_trade_email_async,send_password_reset_email
from rest_framework import status
# from django.utils.timezone import make_aware
# from django.utils.timezone import localtime
from django.utils.timezone import make_aware, localtime
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
from main.companysmtpsetails import get_company_profile,get_smtp_details 
from rest_framework import permissions
company_profile = get_company_profile()
smtp_details = get_smtp_details()

# from main.companysmtpsetails import smtp_details,company_profile
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime
USER_ID=config('USER_ID')
ALICE_API_KEY=config('ALICE_API_KEY')
import logging
logger = logging.getLogger('main')
UserModel = get_user_model()


company_profile = company_profile
# company_profile=None
support_email = company_profile.company_support_email if company_profile else "support@example.com"
company_website = company_profile.company_website if company_profile else "https://example.com"
logo_url = company_profile.company_logo if company_profile else "https://example.com/logo.png"
login_link = company_profile.login_link if company_profile else "https://www.admin.algoview.in/login"
help_center_link = company_profile.help_center_link if company_profile else "https://www.admin.algoview.in/login"  
contact_number = company_profile.company_phone_number if company_profile else None

smtp_details=smtp_details
default_from_email=smtp_details.email_host_user if smtp_details else   "no-reply@example.com" 
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
# class CustomLoginView(generics.GenericAPIView):
#     pagination_class = None
#     serializer_class = CustomLoginSerializer
#     def post(self, request, *args, **kwargs):
#         # start_time=time.time()
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         # end_time = time.time()  # Record the end time
#         # execution_time = end_time - start_time  # Calculate the total time
#         # print(f"Login API executed in {execution_time:.4f} seconds")  # Log the execution timee
#         return Response(serializer.validated_data, status=status.HTTP_200_OK)

class CustomLoginView(generics.GenericAPIView):
    pagination_class = None
    serializer_class = CustomLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get('user')

        # Log the login time in UserActivityLog
        UserActivityLog.objects.create(
            user=user,
            last_login_time=now(),
            session_key=request.session.session_key
        )

        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    
#logout api
# class LogoutView(APIView):
#     permission_classes = [IsAuthenticated]  # Ensure user is authenticated

#     def post(self, request):
#         # Get user's refresh token from request data (passed by frontend)
#         refresh_token = request.data.get('refresh_token')
        
#         try:
#             # Blacklist the refresh token (if using Simple JWT Blacklisting)
#             token = RefreshToken(refresh_token)
#             token.blacklist()

#             # Log the user's logout time in the UserActivityLog
#             session_key = request.session.session_key
#             try:
#                 activity_log = UserActivityLog.objects.filter(user=request.user,session_key=session_key).latest('last_login_time')
#                 activity_log.mark_logout()
#             except UserActivityLog.DoesNotExist:
#                 pass  # If no login entry exists, skip silently
            
#             return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def post(self, request):
        refresh_token = request.data.get('refresh_token')

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Log the user's logout time in the UserActivityLog
            session_key = request.session.session_key
            try:
                activity_log = UserActivityLog.objects.filter(user=request.user, session_key=session_key).latest('last_login_time')
                if not activity_log.last_logout_time:  # Ensure logout is only recorded once
                    activity_log.last_logout_time = now()
                    activity_log.save()
            except UserActivityLog.DoesNotExist:
                pass  # If no login entry exists, skip silently

            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

from django.utils.timezone import now


class UserActivityLogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id = request.GET.get('user_id')  # Get user ID from query parameters

        # If user_id is provided, check if the current user is allowed to view it
        if user_id and not request.user.is_client:
            return Response({"error": "You are not authorized to view other users' activity."}, status=status.HTTP_403_FORBIDDEN)

        # If no user_id is provided, fetch the logged-in user's data
        user = UserModel.objects.get(id=user_id) if user_id else request.user

        # Fetch the most recent completed session (login + logout recorded)
        last_completed_session = (
            UserActivityLog.objects
            .filter(user=user, last_login_time__isnull=False, last_logout_time__isnull=False)
            .order_by('-last_login_time')
            .first()
        )

        # Fetch the most recent login entry (latest login without logout)
        current_login_session = (
            UserActivityLog.objects
            .filter(user=user, last_login_time__isnull=False)
            .order_by('-last_login_time')
            .first()
        )

        response_data = {}

        if last_completed_session:
            response_data["last_login_time"] = last_completed_session.last_login_time.astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            response_data["last_logout_time"] = last_completed_session.last_logout_time.astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        if current_login_session:
            response_data["current_login_time"] = current_login_session.last_login_time.astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        if response_data:
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({"message": "No login/logout data found."}, status=status.HTTP_404_NOT_FOUND)

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
            # self.send_email_otp(user.email, otp.otp_code)
            resend_otp_email_async.delay(user.email, otp.otp_code)
            return Response(
                {"success": "A new OTP has been sent to your email."},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)

    def send_email_otp(self, email, otp_code):
        subject = 'Your OTP Code'
        message = f'Your OTP code is {otp_code}.'
        from_email = default_from_email
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
            # reset_link = f'https://sparks.algoview.in/pages/authentication/reset-password/:{uid}/:{token}/:layout'
            # reset_link = f'https://www.admin.algoview.in/pages/authentication/reset-password/:{uid}/:{token}/:layout'
            # reset_link = f'http://103.120.178.54:4000/pages/authentication/reset-password/:{uid}/:{token}/:layout'
            # reset_link = f'http://localhost:3000/pages/authentication/reset-password/:{uid}/:{token}/:layout'
            # subject = "Password Reset Request"
            # print("reset_link",reset_link)
            # message = (
            #     f"Hello,\n\n"
            #     f"You've requested a password reset. Click the link below to reset your password:\n"
            #     f"{reset_link}\n\n"
            #     f"If you did not request this, please ignore this email.\n\n"
            #     f"Best regards,\nYour Team"
            # )
            # send_mail(subject, message, from_email, [email])
            # Retrieve the default from email from your SMTP settings.
            dynamic_email = default_from_email 
            username = user.firstName
            print("default_from_email>>>>", dynamic_email)
            send_password_reset_email(uid,email,username ,token)
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
            logger.info(f"Admin:::{user.role.name}")
        search_query = request.query_params.get('q', '').strip()
        if search_query:
            users = users.filter(
                Q(firstName__icontains=search_query) |
                Q(phoneNumber__icontains=search_query) |
                Q(email__icontains=search_query)
            )
    
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
# class UserProfileView(APIView):
#     pagination_class = None
#     permission_classes = [IsAuthenticated]
#     def get(self, request, *args, **kwargs):

#         try:
#             user = request.user
#             serializer = UserProfileRetrieveSerializer(user)
#             return Response(serializer.data)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def patch(self, request, *args, **kwargs):
#         user = request.user
#         try:
#             # Start transaction in case of complex updates (optional)
#             with transaction.atomic():
#                 print("____________",request.data)
#                 serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
#                 if serializer.is_valid():
#                     serializer.save()
#                     return Response(serializer.data, status=status.HTTP_200_OK)
#                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#         except ValidationError as ve:
#             return Response({"validation_error": ve.detail}, status=status.HTTP_400_BAD_REQUEST)
#         except ObjectDoesNotExist:
#             return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserProfileView(APIView):
    pagination_class = None
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            serializer = UserProfileRetrieveSerializer(user)
            
            # Add `user_id` explicitly in response
            response_data = serializer.data
            response_data["client"] = user.id

            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, *args, **kwargs):
        user = request.user
        try:
            with transaction.atomic():
                print("____________", request.data)
                serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    
                    # Add `user_id` in update response
                    response_data = serializer.data
                    response_data["client"] = user.id

                    return Response(response_data, status=status.HTTP_200_OK)
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
    

from rest_framework.exceptions import NotFound
from rest_framework.pagination import LimitOffsetPagination



# class PendingKYCListView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         try:           

#             # Fetch all pending KYC requests
#             pending_kycs = KYC.objects.all().order_by('-id')
#             search_query = request.GET.get('q', '')

#             if search_query:
#                 pending_kycs = pending_kycs.filter(
#                     Q(user__fullName__icontains=search_query) |
#                     Q(user__firstName__icontains=search_query) |
#                     Q(user__lastName__icontains=search_query)
#                 )

#             if not pending_kycs.exists():
#                 return Response({"message": "No KYC requests found."}, status=status.HTTP_200_OK)

#             paginator = CustomPageNumberPagination()
            
#             try:
#                 result_page = paginator.paginate_queryset(pending_kycs, request)
#                 if not result_page:
#                     return Response({"message": "No KYC requests found."}, status=status.HTTP_200_OK)
#             except NotFound:  # Handle invalid page numbers
#                 return Response({"message": "No KYC requests found."}, status=status.HTTP_200_OK)

#             serializer = KYCSerializer(result_page, many=True)
#             return paginator.get_paginated_response(serializer.data)

#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# correct code 

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.http import urlencode 

class PendingKYCListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Fetch all KYC records (filter for pending ones if needed)
            pending_kycs = KYC.objects.all().order_by('-id')

            # Get the search query from the request
            search_query = request.GET.get('q', '').strip()

            # Apply search filter if a search query is provided
            if search_query:
                pending_kycs = pending_kycs.filter(
                    Q(user__firstName__icontains=search_query) | 
                    Q(user__lastName__icontains=search_query) | 
                    Q(user__fullName__icontains=search_query)
                )

            # 🔹 Debug: Print filtered count
            print(f"Filtered pending KYCs count: {pending_kycs.count()}")


            # ✅ Allow dynamic page size (default=10, options: 10, 25, 50)
            allowed_page_sizes = [10, 25, 50]  # Allowed values
            try:
                items_per_page = int(request.GET.get('page_size', 10))  # Get page_size from request
                if items_per_page not in allowed_page_sizes:  
                    items_per_page = 10  # If invalid, fallback to default
            except ValueError:
                items_per_page = 10  # If conversion fails, fallback to default

            # Pagination parameters
            page = request.GET.get('page_number', 1)
            paginator = Paginator(pending_kycs, items_per_page)
            paginated_kycs = paginator.get_page(page)  # Auto-handles invalid pages


            # Serialize the paginated queryset
            serializer = KYCSerializer(paginated_kycs, many=True)

            # Preserve query parameters
            query_params = request.GET.copy()
            base_url = request.build_absolute_uri(request.path)

            next_page = None
            prev_page = None

            if paginated_kycs.has_next():
                query_params['page'] = paginated_kycs.next_page_number()
                next_page = f"{base_url}?{urlencode(query_params)}"

            if paginated_kycs.has_previous():
                query_params['page'] = paginated_kycs.previous_page_number()
                prev_page = f"{base_url}?{urlencode(query_params)}"

            return Response({
                "count": paginator.count,
                "next": next_page,
                "previous": prev_page,
                "results": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        from_email = default_from_email,
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
class LastLoginoldActivityView(APIView):
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
            
class LastLoginActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        last_two_login_activities = UserActivityLog.objects.filter(
            user=request.user, action_type='login'
        ).order_by('-last_login_time')[:2]

        if not last_two_login_activities:
            return Response({"error": "No login activity found."}, status=404)

        # If only one record exists, return that, otherwise return the second most recent login
        last_login_activity = last_two_login_activities[0] if len(last_two_login_activities) == 1 else last_two_login_activities[1]

        response_data = {
            'last_login_time': last_login_activity.last_login_time,
            'last_ip': last_login_activity.ip_address,
            'session_key': last_login_activity.session_key,
            # 'is_logged_out': last_login_activity.logout_time is not None,
        }

        return Response(response_data)
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
        search_query = request.query_params.get('q', '').strip()
        if search_query:
            segments = segments.filter(Q(name__icontains=search_query)|
                                       Q(status__icontains=search_query)|
                                       Q(short_name__icontains=search_query))
            
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
        search_query = request.query_params.get('q', '').strip()
        if search_query:
            category_list = category_list.filter(Q(name__icontains=search_query))
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
        search_query = request.query_params.get('q', '').strip()
        if search_query:
            services = services.filter(Q(service_name__icontains=search_query))
            
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
            search_query = request.query_params.get('q', '').strip()
            group_ser = group_ser.filter(
                Q(group_name__icontains=search_query) 
            )
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
        search_query = request.query_params.get('q', '').strip()
        if search_query:
            strategies = strategies.filter(Q(name__icontains=search_query))
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
            search_query = request.query_params.get('q', '').strip()
            if search_query:
                brokers = brokers.filter(Q(broker_name__icontains=search_query))
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
                # Get the search query from request params
        search_query = request.query_params.get('q', '').strip()

        # If a search query is provided, search across multiple fields
        if search_query:
            clients = clients.filter(
                Q(userName__icontains=search_query) |
                Q(fullName__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phoneNumber__icontains=search_query)
            )
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
        search_query = request.query_params.get('q', '').strip()

        # If a search query is provided, search across multiple fields
        if search_query:
            clients = clients.filter(
                Q(userName__icontains=search_query) |
                Q(fullName__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phoneNumber__icontains=search_query)
            )        
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
                group_name = client.Group_service.group_name if hasattr(client, "Group_service") else None

                for subsegment_id in subsegments:
                    trade_settings_data = {
                        "client": client.id,
                        "segment": segment_id,
                        "sub_segment": subsegment_id,
                        "group_service": group_name,
                        
                        # Add any other fields required for ClientTradeSetting
                    }
                    trade_setting_serializer = ClientTradeSettingSerializer(data=trade_settings_data)
                    print("trade_setting_serializer>>>",trade_setting_serializer)
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
            # new_group_service_id = request.data.get("Group_service")  # New group service ID from request
            # print("new_group_service>>>>", new_group_service_id)

            # # Get the new group service name using the ID
            # if new_group_service_id:
            #     try:
            #         new_group_service = GroupService.objects.get(id=new_group_service_id)
            #         new_group_service_name = new_group_service.group_name
            #         print("New Group Service Name:", new_group_service_name)
            #     except GroupService.DoesNotExist:
            #         return Response({"error": "Group Service not found"}, status=status.HTTP_404_NOT_FOUND)
            # else:
            #     new_group_service_name = None

            # Get the existing group service name (if any)
            
            # Get the new group service name
            new_group_service_name = getattr(client.Group_service, "group_name", None)
            existing_group_service_name=None
            # new_group_service_name = client.Group_service.group_name if hasattr(client, "Group_service") else None
            print("new_group_service_name::::", new_group_service_name, "new group service name>>>>***********", new_group_service_name)

            # Get the existing group service name from the last ClientTradeSetting object
            last_trade_setting = ClientTradeSetting.objects.filter(client=client).last()
            if last_trade_setting:
                existing_group_service_name = last_trade_setting.group_service if last_trade_setting else None
                print("existing_group_service_name>>>>", existing_group_service_name)
                # If the new group service is different from the existing one
                if segment_id and subsegments:
                    if new_group_service_name != existing_group_service_name:
                    
                        # Delete old trade settings for the existing group service
                        trade=ClientTradeSetting.objects.filter(client=client).delete()
                        print("delted ordersssssssssss",trade)
                        # Create new trade settings for the new group service
                        for subsegment_id in subsegments:
                            trade_setting, created = ClientTradeSetting.objects.update_or_create(
                                client=client,
                                segment_id=segment_id,
                                sub_segment_id=subsegment_id,
                                defaults={"group_service": new_group_service_name}  # Update or create with new group service
                            )
                            print("trade_setting new>>>", trade_setting)
                            if created:
                                print(f"Created new trade setting for {client} - {segment_id} - {subsegment_id} with group service {new_group_service_name}")
                            else:
                                print(f"Updated existing trade setting for {client} - {segment_id} - {subsegment_id} with group service {new_group_service_name}")
                    else:
                        # print(">>>>>>>>>>sdjfsjfjsfisfsifiLLLLLLLLLLLLLLLLL")
                        # If the group service is the same, update existing trade settings
                        for subsegment_id in subsegments:
                            # trade=ClientTradeSetting.objects.filter(client=client).delete()
                            trade_setting, created = ClientTradeSetting.objects.update_or_create(
                                client=client,
                                segment_id=segment_id,
                                sub_segment_id=subsegment_id,
                                defaults={"group_service": existing_group_service_name}  # Update existing settings
                            )
                            print("trade_setting is updated  >>>", trade_setting)
                            if created:
                                print(f"Created new trade setting for {client} : {segment_id} : {subsegment_id} with group service {existing_group_service_name}")
                            else:
                                print(f"Updated existing trade setting for {client} : {segment_id} : {subsegment_id} with group service {existing_group_service_name}")

            else:
                for subsegment_id in subsegments:
                        
                    trade_setting, created = ClientTradeSetting.objects.update_or_create(
                        client=client,
                        segment_id=segment_id,
                        sub_segment_id=subsegment_id,
                        defaults={"group_service": existing_group_service_name}  # Update existing settings
                    )
                    print("trade_setting is updated  >>>", trade_setting)
                    if created:
                        print(f"Created new trade setting for {client} : {segment_id} : {subsegment_id} with group service {existing_group_service_name}")
                    else:
                        print(f"Updated existing trade setting for {client} : {segment_id} : {subsegment_id} with group service {existing_group_service_name}")

                
            return Response(ClientListSerializer(client).data, status=status.HTTP_200_OK)
        
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


class ClientOnboardingStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Get the filter type from the request
            filter_type = request.GET.get('filter', None)
            today = datetime.now().date()
            start_date = None
            end_date = None

            # If no filter type is provided, return a response with null values
            if filter_type is None:
                return Response({
                    "filter_type": None,
                    "client_count": 0,
                    "start_date": None,
                    "end_date": None,
                    "data": []
                }, status=200)

            # Determine the date range based on the filter type
            if filter_type == 'today':
                start_date = today
                end_date = today
            elif filter_type == 'yesterday':
                start_date = today - timedelta(days=1)
                end_date = today - timedelta(days=1)
            elif filter_type == 'this_week':
                start_date = today - timedelta(days=today.weekday())  # Start of the week
                end_date = today
            elif filter_type == 'this_month':
                start_date = today.replace(day=1)  # Start of the month
                end_date = today
            elif filter_type == 'date_range':
                # Get custom date range from query parameters
                from_date = request.GET.get('from_date', None)
                to_date = request.GET.get('to_date', None)
                if from_date and to_date:
                    start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
                    end_date = datetime.strptime(to_date, "%Y-%m-%d").date()
                else:
                    return Response({"message": "Both from_date and to_date are required for date range."}, status=400)
            else:
                return Response({"error": "Invalid filter type."}, status=400)

            # Query to count clients created within the specified date range
            client_counts = (
                User.objects
                .filter(
                    created_at__date__range=(start_date, end_date),
                    type_of_user='is_client'  # Filter to include only clients
                )
                .extra({'created_date': 'date(created_at)'})  # Extract the date part
                .values('created_date')  # Group by the created date
                .annotate(clients=Count('id'))  # Count clients for each date
                .order_by('created_date')  # Order by date
            )

            # Prepare the response data
            response_data = {
                "filter_type": filter_type,
                "start_date": start_date,
                "end_date": end_date,
                "data": [
                    {"date": entry['created_date'], "clients": entry['clients']}
                    for entry in client_counts
                ]
            }

            # Calculate total client count
            total_client_count = sum(entry['clients'] for entry in client_counts)

            # Add total client count to the response
            response_data["client_count"] = total_client_count

            return Response(response_data, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class ClientTradingStatusCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Determine which clients to include based on user role
        if user.role and user.role.name.lower() == 'super-admin':
            # Super-admin can see all clients
            clients = User.objects.filter(type_of_user='is_client', is_client=True)
        elif user.role and user.role.name.lower() == 'sub-admin':
            # Sub-admin can see only their assigned clients
            clients = User.objects.filter(assigned_client=user, type_of_user='is_client', is_client=True)
        else:
            # If the user is neither super-admin nor sub-admin, return an empty response or handle accordingly
            return Response({"detail": "You do not have permission to view this data."}, status=403)

        # Count active and inactive clients based on the is_enable field
        active_count = clients.filter(is_enable=True).count()
        inactive_count = clients.filter(is_enable=False).count()

        # Prepare the response data
        response_data = {
            "active_clients": active_count,
            "inactive_clients": inactive_count
        }

        return Response(response_data, status=200)


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

            # Apply search filter
            search_query = request.query_params.get('q', '').strip()
            if search_query:
                expiry_client = expiry_client.filter(
                    Q(firstName__icontains=search_query) |
                    Q(email__icontains=search_query) |
                    Q(phoneNumber__icontains=search_query)
                )

            # Apply pagination
            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(expiry_client, request)

            # Serialize the paginated data
            serializer = ClientListSerializer(result_page, many=True)

            # Return paginated response
            return paginator.get_paginated_response({"expiry_client_list": serializer.data})

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
        search_query = request.query_params.get('q', '').strip()    
        clients = clients.filter(
            Q(firstName__icontains=search_query) |
            Q(phoneNumber__icontains=search_query) | 
            Q(email__icontains=search_query)
        )

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
        search_query = request.query_params.get('q', '').strip()    
        clients = clients.filter(
            Q(firstName__icontains=search_query) |
            Q(phoneNumber__icontains=search_query) |  
            Q(email__icontains=search_query)
        )

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
def place_order_broker(LivePrice,group_service,
    trade, user, transaction_type, symbol, quantity, strategy, ordertype,product_type, price, Lots, 
    trade_order_status, Entry_type, Exit_type, Entry_price,Exit_price,EntryQty,ExitQty,
    webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice, day, month, year, fullyear,default_price, Type, order_params):
    order_id = 0
    response = {"data": {"status": "Failed", "message": "Unsupported broker or no broker matched"}}
   
    print(" rgdaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaae", Entry_price, Exit_price,)
    # Initialize response with a default failure value
    response = {"data": {"status": "Failed", "message": "Unsupported broker or no broker matched"}}
    status = "Failed"
    res_data = "Unknown response"
    message=""

    if trade['broker'].lower() == "fyers":
        symbol=symbol.upper()
        print("day>>>>>>>>>>>",day)
        trade_symbol = f"{symbol}{year}{month}{day}{default_price}{Type}"
        logger.info(f"{user} : trading_symbol OF Fyers..:::::: %s ", trade_symbol)
        client_broker = ClientBrokerdetails.objects.filter(client=trade['client'], broker_name__broker_name__iexact=trade['broker']).first()
        if not client_broker:
            message = f"No broker details found for client {trade['client']} and broker {trade['broker']}"
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user, trade_symbol, order_id, status, res_data, message, strategy,Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty, webhook_signal, Exchange, Segment, Index_Symbol,order_params, broker="fyers"
            )
            logger.error(message)
            return {"data": {"status": "Failed", "message": message}}
        access_token=client_broker.access_token
        Api_key=client_broker.broker_API_KEY
        print("fyers access token","Api_key.....",Api_key)
        if not access_token or not Api_key:
            message = f"API credentials  token not found for client {trade['client']} and broker {trade['broker']}."
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user, trade_symbol, order_id, status, res_data, message, strategy,
                Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal, Exchange, Segment, Index_Symbol,
                order_params, broker="fyers"
            )
            logger.error(message)
            return {"data": {"status": "Failed", "message": message}}

        # logger.info(f"Fetched API credentials for broker {trade['broker']}.")
        logger.info(f"{user} : Placing order for user: {user}, Broker: {trade['broker']}, Symbol: {trade['symbol']}")
        if transaction_type == "SELL":
            response = exit_existing_buy_position_fyers_order(default_price,LivePrice,group_service,Type,day,month,year,access_token,Api_key,trade_symbol, transaction_type, symbol, quantity,strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type,Entry_price,Exit_price,
                EntryQty,ExitQty,webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice,trade_order_status)

            if response.get("data", {}).get("status") == "error" or response.get("data", {}).get("status") == "Failed":
                message = response.get("data", {}).get("message", f"Existing BUY position for {symbol} could not be closed.")
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user, trade_symbol, order_id, status, res_data, message, strategy,
                    Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal, Exchange, Segment, Index_Symbol,
                    order_params, broker="fyers"
                )
                logger.error(message)
                return {"data": {"status": "Failed", "message": message}} 
        if transaction_type =="BUY":
                response = place_fyers_orders(LivePrice,group_service,access_token,Api_key,trade_symbol, transaction_type, symbol, quantity,
                    strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type,Entry_price,Exit_price,
                    EntryQty,ExitQty,webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice,trade_order_status)
                
        logger.info(f"{user} : fyers Order Response: {response}")
        
    elif trade['broker'].lower() == "dhan":
        symbol=symbol.upper()
        """
            Creates a trading symbol in the format: SYMBOL+MONTH+YEAR+STRIKE+TYPE
            Example: POWERGRIDMAR2025410PE or NIFTYMAR202522600CE
        """
        
        symbol = symbol.upper()
        print("dhan fun   calleddddddddd", symbol)
        month_number = datetime.strptime(month, "%b").month
        expiry_date = f"{fullyear}-{month_number:02d}-{day}"
        print("expiry_date>>>>>",expiry_date)      
        trade_symbol = f"{symbol}{month}{fullyear}{default_price}{Type}"     
        # trade_symbol = f"{symbol}{day}{month}{default_price}{Type}" 
        print(">>>>>>>trade_symbol DHANNNNNNNNNNNN>>>>>>>>>>>",trade_symbol)
        # Fetch client broker details
        client_broker = ClientBrokerdetails.objects.filter(client=trade['client'], broker_name__broker_name__iexact=trade['broker']).first()
        if not client_broker:
            message= f"No broker details found for client {trade['client']} and broker {trade['broker']}"
            response= {"data":{"status": "Failed", "message":message }}
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message, strategy,  Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal , Exchange, Segment,Index_Symbol, order_params,broker="dhan")
                
            logger.error(f"{user} : No broker details found for client {trade['client']} and broker {trade['broker']}")
            return response # continue

        client_id = client_broker.broker_API_KEY
        print("api key",client_id,"<<<<<<<<<<",client_broker)
        access_token = client_broker.access_token
        if not access_token or not client_id:
            message = f"API credentials not found for client {trade['client']} and broker {trade['broker']}."
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user, trade_symbol, order_id, status, res_data, message, strategy,Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty, webhook_signal, Exchange, Segment, Index_Symbol,order_params, broker="dhan"
            )
            logger.error(message)
            return {"data": {"status": "Failed", "message": message}}
        logger.info(f"{user} : !!!!Placing order for user: {user} Brocker is: {trade['broker']} & trading symbol is: {trade['symbol']} and transaction_type is 99  {transaction_type}")
        if transaction_type=="SELL":
            response = exit_existing_buy_position_DhanOrder(expiry_date,LivePrice,group_service,Type,day,month,fullyear,access_token, client_id, trade_symbol, transaction_type, symbol, quantity,strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty, webhook_signal, Exchange, Segment,Index_Symbol, triggerPrice, trade_order_status)
            # If the exit failed, do not proceed.
            if response.get("data", {}).get("status") == "error":
                message = response.get("data", {}).get("message", f"Existing BUY position for {symbol} could not be closed.")

                # message = f"before place new BUY order please close existing BUY position  {symbol} could not be closed."
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message, strategy,Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty, webhook_signal,Exchange, Segment, Index_Symbol, order_params, broker="dhan")
                logger.error(message)
                return {"data": {"status": "Failed", "message": message}} 
        logger.info(f"{user} : transaction_type ::{transaction_type} use is :{{user}}")
        if transaction_type == "BUY":
            logger.info(f"dhan buy order for user:{user}") 
            response=place_dhan_orders(expiry_date,LivePrice,group_service,access_token, client_id, trade_symbol, transaction_type, symbol, quantity,
                strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type, Entry_price, Exit_price, 
                EntryQty, ExitQty, webhook_signal, Exchange, Segment,Index_Symbol, triggerPrice, trade_order_status)
        logger.info(f"{user} : dhan api. Response: {response} for user :{user}")
        
    elif trade['broker'].lower() == "5paisa":
        symbol=symbol.upper()
        print("5 paisa function is calleddddddddd")
        formated_prc=f"{default_price:.2f}"
        trade_symbol = f"{symbol}{day}{month}{fullyear}{Type}{formated_prc}" 
        print(">>>>>>>trade_symbol 5paisa>>>>>>>>>>>",trade_symbol)
        # Fetch client broker details
        client_broker = ClientBrokerdetails.objects.filter(client=trade['client'], broker_name__broker_name__iexact=trade['broker']).first()
        if not client_broker:
            message= f"{user} : No broker details found for client {trade['client']} and broker {trade['broker']}"
            response= {"data":{"status": "Failed", "message":message }}
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message, strategy,  Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal , Exchange, Segment,Index_Symbol, order_params,broker="5paisa")
            logger.error(f"{user} : No broker details found for client {trade['client']} and broker {trade['broker']}")
            return response # continue

        api_key = client_broker.broker_API_KEY
        # encreption_key = client_broker.broker_API_SKEY
        # user_id = client_broker.broker_API_UID
        access_token = client_broker.access_token
        if not access_token or not api_key:
            message = f"API credentials not found for client {trade['client']} and broker {trade['broker']}."
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user, trade_symbol, order_id, status, res_data, message, strategy,Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty, webhook_signal, Exchange, Segment, Index_Symbol,order_params, broker="5paisa"
            )
            logger.error(message)
            return {"data": {"status": "Failed", "message": message}}
        # logger.info(f"Fetched API credentials for {trade['broker']}: SKEY={api_key}, USER={demate_user_name}")
            # continue  # Skip to next user if token data is not found
        logger.info(f"{user} : !!!!Placing order for user: {user} Brocker is: {trade['broker']} & trading symbol is: {trade['symbol']}")
        if transaction_type == "SELL": 
            response = exit_existing_buy_position_5PaisaOrder(LivePrice,group_service,Type,day,month,fullyear,api_key,access_token,trade_symbol,transaction_type, symbol, quantity,strategy,ordertype,
            product_type, price,user, Lots,trade_order_status,  Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal ,Exchange, Segment,Index_Symbol,triggerPrice,trade)

            # If the exit failed, do not proceed.
            if response.get("data", {}).get("status") == "error":
                message = response.get("data", {}).get("message", f"Existing BUY position for {symbol} could not be closed.")
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message, strategy,Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty, webhook_signal,Exchange, Segment, Index_Symbol, order_params, broker="5paisa")
                logger.error(message)
                return {"data": {"status": "Failed", "message": message}} 
        if transaction_type == "BUY": 
            response=place_5paisa_order(LivePrice,group_service,api_key,access_token,trade_symbol,transaction_type, symbol, quantity,strategy,ordertype,
                product_type, price,user, Lots,trade_order_status,  Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal ,Exchange, Segment,Index_Symbol,triggerPrice,trade)

        logger.info(f"{user} : 5paisa blue. Response: {response}")
        
    elif trade['broker'].lower() == "zerodha":
        symbol=symbol.upper()
        trade_symbol = f"{symbol}{year}{month}{default_price}{Type}"
        print("Trading Symbol zerodha: ", symbol)
        # Fetch client broker details
        client_broker = ClientBrokerdetails.objects.filter(client=trade['client'], broker_name__broker_name__iexact=trade['broker']).first()
        if not client_broker:
            message = f"No broker details found for client {trade['client']} and broker {trade['broker']}"
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user, trade_symbol, order_id, status, res_data, message, strategy,Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty, webhook_signal, Exchange, Segment, Index_Symbol,order_params, broker="zerodha"
            )
            logger.error(message)
            return {"data": {"status": "Failed", "message": message}}
        access_token=client_broker.access_token
        Api_key=client_broker.broker_API_KEY
        print("zerodha access token",access_token,"Api_key.....",Api_key)
        if not access_token or not Api_key:
            message = f"API credentials  token not found for client {trade['client']} and broker {trade['broker']}."
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user, trade_symbol, order_id, status, res_data, message, strategy,
                Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal, Exchange, Segment, Index_Symbol,
                order_params, broker="zerodha"
            )
            logger.error(message)
            return {"data": {"status": "Failed", "message": message}}

        # logger.info(f"Fetched API credentials for broker {trade['broker']}.")
        logger.info(f"{user} : Placing order for user: {user}, Broker: {trade['broker']}, Symbol: {trade['symbol']}")
        if transaction_type == "SELL":
            response = exit_existing_buy_position_zerodha_order(LivePrice,group_service,Type,day,month,year,access_token,Api_key,trade_symbol, transaction_type, symbol, quantity,strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type,Entry_price,Exit_price,
                EntryQty,ExitQty,webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice,trade_order_status)

            if response.get("data", {}).get("status") == "error" or response.get("data", {}).get("status") == "Failed":
                message = response.get("data", {}).get("message", f"Existing BUY position for {symbol} could not be closed.")
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user, trade_symbol, order_id, status, res_data, message, strategy,
                    Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal, Exchange, Segment, Index_Symbol,
                    order_params, broker="zerodha"
                )
                logger.error(message)
                return {"data": {"status": "Failed", "message": message}} 
        if transaction_type =="BUY":
                response = place_zerodha_orders(LivePrice,group_service,access_token,Api_key,trade_symbol, transaction_type, symbol, quantity,
                    strategy, ordertype, product_type, price, user, Lots, Entry_type, Exit_type,Entry_price,Exit_price,
                    EntryQty,ExitQty,webhook_signal, Exchange, Segment, Index_Symbol, triggerPrice,trade_order_status)
            
        logger.info(f"{user} : Zerodha Order . Response: {response}")

    elif trade['broker'].lower() == "upstox":
        symbol=symbol.upper()
        trade_symbol = f"{symbol}{default_price}{Type}{day}{month}{year}"
        logger.info(f"{user} : Trading Symbol (Upstox): {trade_symbol}")
        broker="upstox"
        client_broker = ClientBrokerdetails.objects.filter(client=trade['client'], broker_name__broker_name__iexact=trade['broker']).first()
        if not client_broker:
            message = f"No broker details found for client {trade['client']} and broker {trade['broker']}."
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user, trade_symbol, order_id, status, res_data, message, strategy,Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty, webhook_signal, Exchange, Segment, Index_Symbol,order_params, broker="Upstox"
            )
            logger.error(message)
            return {"data": {"status": "Failed", "message": message}}

        # api_skey = client_broker.broker_API_SKEY
        # api_uid = client_broker.broker_API_KEY
        access_token = client_broker.access_token
  
        if not access_token: #or not api_skey or not api_uid:
            message = f"API credentials  token not found for client {trade['client']} and broker {trade['broker']}."
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user, trade_symbol, order_id, status, res_data, message, strategy,Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal, Exchange, Segment, Index_Symbol,order_params, broker="Upstox"
            )
            logger.error(message)
            return {"data": {"status": "Failed", "message": message}}

        # Placing the order
        # try:
        logger.info(f"{user} : Placing order for user: {user}, Broker: {trade['broker']}, Symbol: {symbol}.transaction_type--{transaction_type}")


        if transaction_type.upper() == "SELL":
            logger.info(f" {user} : SELL transaction type##########")
            response = exit_existing_buy_position_Upstox(group_service,LivePrice,Type,day,month,year,access_token, trade_symbol, transaction_type,symbol, quantity, strategy, ordertype, product_type, price, user,Lots, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty, webhook_signal, Exchange, Segment,Index_Symbol, triggerPrice,trade_order_status)
            # If the exit failed, do not proceed.
            if response.get("data", {}).get("status") == "error":
                message = response.get("data", {}).get("message", f"Existing BUY position for {symbol} could not be closed.")

                # message = f"before place new BUY order please close existing BUY position  {symbol} could not be closed."
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message, strategy,Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty, webhook_signal,Exchange, Segment, Index_Symbol, order_params, broker="Upstox")
                logger.error(message)
                return {"data": {"status": "Failed", "message": message}} 
        if transaction_type.upper() == "BUY":
            response = place_upstox_orders(LivePrice,group_service,
                access_token, trade_symbol, transaction_type,symbol, quantity, strategy, ordertype, product_type, price, user,
                Lots, Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty, webhook_signal, Exchange, Segment,
                Index_Symbol, triggerPrice,trade_order_status
            )
        
        logger.info(f"{user} : Upstox  Order. Response: {response}")

        #     return response
        # except Exception as e:
        #     # Handle unexpected errors during order placement
        #     message = f"An error occurred while placing the order: {str(e)}"
        #     save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,
        #         user, trade_symbol, order_id, status, res_data, message, strategy,
        #         Entry_type, Exit_type, webhook_signal, Exchange, Segment, Index_Symbol,
        #         order_params, broker="Upstox"
        #     )
        #     logger.error(message)
        #     return {"data": {"status": "Failed", "message": message}}
  
    elif trade['broker'].lower() == "alice blue":
        print("alice blue is matchedddddddddddddddddd")
        symbol=symbol.upper()
        trading_symbol_aliceblue = f"{symbol}{day}{month}{year}{Type[0]}{default_price}"
        logger.info(f"{user} : trading_symbol_aliceblue..:::::: %s ", trading_symbol_aliceblue)
        trade_symbol=trading_symbol_aliceblue
        # Fetch client broker details
        client_broker = ClientBrokerdetails.objects.filter(client=trade['client'], broker_name__broker_name__iexact=trade['broker']).first()
        if not client_broker:
            message= f"No broker details found for client {trade['client']} and broker {trade['broker']}"
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy, Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal , Exchange, Segment,Index_Symbol,order_params,broker="Alice Blue")
            logger.error(f"{user} : No broker details found for client {trade['client']} and broker {trade['broker']}")
            response= {"data":{"status": "Failed", "message":message }}
            return response

        api_skey = client_broker.broker_API_KEY
        api_uid = client_broker.broker_API_UID
        if not api_skey or not api_uid:
            message = f"API credentials not found for client {trade['client']} and broker {trade['broker']}."
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user, trade_symbol, order_id, status, res_data, message, strategy,
                Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty, webhook_signal, Exchange, Segment, Index_Symbol,
                order_params, broker="Alice Blue"
            )
            logger.error(message)
            return {"data": {"status": "Failed", "message": message}}
        logger.info(f"{user} : Fetched API credentials for {trade['broker']}: SKEY={api_skey}, UID={api_uid}")

        logger.info(f"{user} : !!!!Placing order for user: {user} Brocker is: {trade['broker']} & trading symbol is: {trade['symbol']} and transaction_type is 99  {transaction_type}")
        if transaction_type.upper() == "SELL":
            logger.info(f"{user} : ALICE BLUE SELLL ORDER:::")
            response = exit_existing_buy_position_Aliceblue(LivePrice,group_service,Type,day,month,year,api_skey,api_uid,trade_symbol,transaction_type, symbol, quantity,strategy,ordertype,
                product_type, price,user, Lots,trade_order_status,  Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,
                ExitQty,webhook_signal ,Exchange, Segment,Index_Symbol,triggerPrice)
            # If the exit failed, do not proceed.
            if response.get("data", {}).get("status") == "error" or response.get("data", {}).get("status") == "Failed":
                message = response.get("data", {}).get("message", f"Existing BUY position for {symbol} could not be closed.")
                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message, strategy,
                                        Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty, webhook_signal,
                                        Exchange, Segment, Index_Symbol, order_params, broker="Alice Blue")
                logger.error(message)
                return {"data": {"status": "Failed", "message": message}} 
        if transaction_type.upper() == "BUY":
            logger.info(f"{user} : alice blue buy order for user:{user}") 
            response=place_alice_orders(LivePrice,group_service,api_skey,api_uid,trade_symbol,transaction_type, symbol, quantity,strategy,ordertype,
            product_type, price,user, Lots,trade_order_status,  Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal ,Exchange, Segment,Index_Symbol,triggerPrice)
        logger.info(f"{user} : Alice blue. Response: {response} for user :::{user}")
    elif trade['broker'].lower() == "angle one":
        broker="Angle One"
        trade_symbol = f"{symbol}{day}{month}{year}{default_price}{Type}" 
        logger.info(f"{user} : Angle one trading symbol is created:::::{trade_symbol}")
        # Fetch client broker details
        client_broker = ClientBrokerdetails.objects.filter(client=trade['client'], broker_name__broker_name__iexact=trade['broker']).first()
        if not client_broker:
            message= f"No broker details found for client {trade['client']} and broker {trade['broker']}"
            response= {"data":{"status": "Failed", "message":message }}
            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message, strategy,  Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal , Exchange, Segment,Index_Symbol, order_params,broker="Angle One")
                
            logger.error(f"{user} : No broker details found for client {trade['client']} and broker {trade['broker']}")
            return response # continue

        api_key = client_broker.broker_API_KEY
        demate_user_name = client_broker.broker_Demate_User_Name
        totp = client_broker.broker_Totp_Authcode
        angle_pass = client_broker.broker_pass
        logger.info(f"user of angle one is {user}")
        if not api_key or not demate_user_name or not totp or not angle_pass:
            message = f"API credentials not found for client {trade['client']} and broker {trade['broker']}."
            save_trade_order_history(LivePrice,group_service,transaction_type,
                trade_order_status,user, trade_symbol, order_id, status, res_data, message, strategy,
                Entry_type, Exit_type,Entry_price,Exit_price,EntryQty,ExitQty, webhook_signal, Exchange, 
                Segment, Index_Symbol,order_params, broker="Angle One"
            )
            logger.error(message)
            return {"data": {"status": "Failed", "message": message}}
        logger.info(f"{user} : Fetched API credentials for {trade['broker']}: SKEY={api_key}, USER={demate_user_name}")

        logger.info(f"{user} : !!!!Placing order for user: {user} Brocker is: {trade['broker']} & trading symbol is: {trade['symbol']} trtransaction_type: {transaction_type}")
        logger.info(f"{user} : trade_symbol of angle order is: {trade_symbol}")
        # continue  # Skip to next user if token data is not found
        # Place order for Angle One
        print("Entry_pric*************************",Entry_price,Exit_price)
        if transaction_type.upper() == "SELL":
            response = exit_existing_buy_position_angleone(client_broker=client_broker,group_service=group_service,LivePrice=LivePrice,Type=Type,day=day,month=month,year=year,
                api_key=api_key,demate_user_name=demate_user_name,totp=totp,angle_pass=angle_pass,
                usertrade=trade,tradingsymbol=trade_symbol,quantity=quantity,product_type=product_type, 
                transactiontype=transaction_type,price=price,ordertype=ordertype,lot_size=Lots,
                Entry_type=Entry_type, Exit_type=Exit_type,Entry_price=Entry_price,Exit_price=Exit_price,EntryQty=EntryQty,ExitQty=ExitQty,
                webhook_signal=webhook_signal,Exchange=Exchange,Segment=Segment,trade_order_status=trade_order_status,
                Index_Symbol=Index_Symbol , user=user, strategy=strategy)                                               
            # If the exit failed, do not proceed.
            # print("response>>>>>>",response)
            if response.get("data", {}).get("status") == "error":
                message = response.get("data", {}).get("message", f"Existing BUY position for {symbol} could not be closed.")

                # message = f"before place new BUY order close existing BUY position {symbol} could not be closed."
                # save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status, user, trade_symbol, order_id, status, res_data, message, strategy,
                #                         Entry_type, Exit_type, Entry_price, Exit_price, EntryQty, ExitQty, webhook_signal,
                #                         Exchange, Segment, Index_Symbol, order_params, broker="Angle One")
                logger.error(message)
                return {"data": {"status": "Failed", "message": message}} 
        if transaction_type.upper() == "BUY":
            logger.info(f"{user} : angle one buy order for user: {user}")
            response =place_Angle_order(client_broker,LivePrice,group_service,api_key=api_key,demate_user_name=demate_user_name,totp=totp,
                angle_pass=angle_pass,usertrade=trade,tradingsymbol=trade_symbol,quantity=quantity,product_type=product_type, 
                transactiontype=transaction_type,price=price,ordertype=ordertype,lot_size=Lots,
                Entry_type=Entry_type, Exit_type=Exit_type,Entry_price=Entry_price,Exit_price=Exit_price,EntryQty=EntryQty,ExitQty=ExitQty,
                webhook_signal=webhook_signal,Exchange=Exchange,Segment=Segment,trade_order_status=trade_order_status,
                Index_Symbol=Index_Symbol , user=user, strategy=strategy)#exch_seg=exch_seg expiry=expiry

        logger.info(f"{user} : Angle one. Response: {response} for user: {user}")    
    return response   

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
# Webhooks-trade-Alert
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
        # default_price = round(float(alert_data.get('signalprice', 0)))   "stratergyid": "Sparks Lite",
        signal_price=alert_data.get('signalprice', 0)
        default_price = round_price(signal_price)
        print("Round of price:::::::::::",default_price)
        strategy_id=alert_data.get('stratergyid', 0)
        logger.info(f"strategy_id get from alert ::::{strategy_id}")
        transaction_type = request.data.get('ordertype', 'BUY-O').upper()
        order_type_mapping = {
            "BUY-O": "Buy CE",
            "SELL-C": "Close CE",
            "SELL-C_O": "Close CE & Buy PE",
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
        print("action_description>>",action_description)
        if action_description=="Close CE & Buy PE":
            buy_sell="CE PE"
        elif action_description =="Close PE & Buy CE":
            buy_sell="PE CE"
        else:    
            action_split = action_description.split()
            transaction_split= transaction_type.split('-')
            buy_sell =action_split[-1]# transaction_split[0]  #  'BUY' or 'SELL'
            # Type = action_split[-1]  # CE or PE
        logger.info(f"buy_sell>>>>{buy_sell}")
        # Map raw symbol to standardized symbol
        symbol_mapping = {
            "NIFTY BANK": "BANKNIFTY",
            "NIFTY 50": "NIFTY",
            "NIFTY FIN SERVICE": "FINNIFTY",
            "MID CAP NIFTY": "MIDCPNIFTY",
            "NIFTY MID SELECT": "MIDCPNIFTY"
        }
        print("raw_symbol")
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
        LivePrice=default_price
        # print("symbols webhook >>>>",symbols)
        webhook_symbols=symbols.upper()
        # producttype=None
        save_webhook_signals_logs(buy_sell, symbols, default_price, strategy, json=alert_data)
        buy_sell_type=transaction_type
        #all_enable_users = ClientTradeSetting.objects.filter(is_tread_status=True,client__is_enable=True, broker__gt='',      			#broker__isnull=False,symbol=webhook_symbols,group_service=strategy_id)
        all_enable_users = ClientTradeSetting.objects.filter(is_tread_status=True,client__is_enable=True,
    		broker__isnull=False,broker__gt='',symbol=webhook_symbols,
    		group_service=strategy_id) # Exclude whitespace-only strings
        
        # Define the field names for the CSV
        fieldnames = [
            'id', 'client', 'segment', 'sub_segment', 'symbol', 'strategy', 'broker',
            'product_type', 'buy_sell', 'quantity', 'trade_limit',
            'max_loss_for_day', 'min_loss_for_day', 'max_profit_for_day',
            'min_profit_for_day', 'current_date', 'group_service', 'expiry_date',
            'is_tread_status', 'sl_type', 'stop_loss', 'target', 'status_flag'
        ]

        csv_file = 'enable_users.csv'
        existing_users = {}

        # Read existing users from CSV if it exists
        if os.path.exists(csv_file):
            with open(csv_file, mode='r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    client_id = row['client']
                    existing_users[client_id] = row  # Save full row

        # Loop through the queryset and prepare/update rows
        for obj in all_enable_users:
            client_id = str(obj.client.id) if obj.client else None
            if not client_id:
                continue  # Skip if no client ID

            row = {}
            for field in fieldnames:
                if field == 'client':
                    row[field] = client_id
                elif field == 'broker':
                    if hasattr(obj.broker, 'id'):
                        row[field] = obj.broker.id
                    else:
                        row[field] = obj.broker or ''
                elif field == 'strategy':
                    if hasattr(obj.strategy, 'id'):
                        row[field] = obj.strategy.id
                    else:
                        row[field] = obj.strategy or ''
                elif field == 'status_flag':
                    row[field] = 'True'  # Always string 'True'
                else:
                    value = getattr(obj, field, None)
                    if isinstance(value, datetime):
                        row[field] = str(value) if value else ''
                    elif isinstance(value, date):
                        row[field] = value.strftime('%Y-%m-%d') if value else ''
                    elif isinstance(value, (int, float, str, bool, type(None))):
                        row[field] = value
                    else:
                        row[field] = str(value)

            # Check if user exists and status_flag is False
            if client_id not in existing_users:
                # If the user doesn't exist, add as a new entry
                print(f"Adding new user: {client_id}")
                existing_users[client_id] = row
            else:
                # User exists, check if 'status_flag' is False
                existing_row = existing_users[client_id]
                if existing_row.get('status_flag') == 'False':
                    print(f"Updating entire row for user: {client_id}")
                    # Update all fields for this user
                    existing_row.update(row)
                else:
                    print(f"User {client_id} is already active, no change.")

        # Write the updated data back to the CSV file
        with open(csv_file, mode='w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            # Write header
            writer.writeheader()
            # Write all rows (including updated ones)
            writer.writerows(existing_users.values())

        print("CSV file has been updated.")

        user_count = all_enable_users.count()
        logger.info(f"=======================================")
        logger.info(f"No. of clients count is {user_count}")
        logger.info(f"=======================================")
        default_expiry=None 
        order_status=None 
        for trade in all_enable_users:
            logger.info(f"all users name is::{trade.client}")

        active_users = []
        if os.path.exists(csv_file):
            with open(csv_file, mode='r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row.get('status_flag') == 'True' and row.get('group_service') == strategy_id:
                        active_users.append(row)
        try:
            for trade in active_users:
                try:
                    transaction_type = buy_sell_type
                    default_expiry = trade['expiry_date']
                    group_service = trade['group_service']
                    trade_order_status = None
                    Entry_price = None
                    Exit_price = None
                    Entry_type = None
                    Exit_type = None
                    EntryQty = None
                    ExitQty = None
                    Type = None
                    trade_symbol = symbols
                    user = trade['client']
                    logger.info('-------------------------------------------------------------------------------------------------------------------------------------')
                    logger.info(f"--------------------{trade['client']} --------------- {trade['symbol']}--------------------")
                    logger.info('-------------------------------------------------------------------------------------------------------------------------------------')
                    Type = None
                    strategy = trade['strategy']
                    Segment = trade['segment']
                    Exchange = exch_seg
                    webhook_signal = alert_data
                    order_id = 0
                    status = "Failed"
                    print(" Entry_price, Exit_price,>>>>>>>>>>>>>>", Entry_price, Exit_price,)
                    Index_Symbol = trade['symbol'] if trade['symbol'] else None
                    res_data = "unknown response"
                    order_params = {
                        "symbol": trade['symbol'] if trade['symbol'] else trade_symbol,
                        "Exchange": exch_seg,
                        "quantity": int(trade['quantity']) or default_quantity,
                        "product_type": trade['product_type'],
                        "transaction_type": buy_sell,
                        "price": limitPrice or 0,
                        "ordertype": default_ordertype,
                        "strategy": trade['strategy']
                    }
                    order_params = serialize_to_json(order_params)

                    print("symbol of trade>>>", trade['symbol'])

                    if not trade['symbol']:
                        logger.error(f"{trade['client']} : Symbol is missing for trade by user {trade['client']}. Skipping this trade.")
                        message = f"Trade skipped due to missing symbol for user {trade['client']}."
                        save_trade_order_history(
                            LivePrice=None,  # 👉 Fill in as per your logic
                            group_service=group_service,
                            transaction_type=transaction_type,
                            trade_order_status=trade_order_status,
                            user=trade['client'],
                            symbol=trade['symbol'],
                            quantity=0,
                            status=status,
                            message=message,
                            strategy=trade['strategy'],
                            Entry_type=Entry_type,
                            Exit_type=Exit_type,
                            Entry_price=Entry_price,
                            Exit_price=Exit_price,
                            EntryQty=EntryQty,
                            ExitQty=ExitQty,
                            webhook_signal=webhook_signal,
                            Exchange=Exchange,
                            Segment=Segment,
                            Index_Symbol=Index_Symbol,
                            order_params=order_params,
                            broker=trade['broker']
                        )
                        continue

                    print("trade.symbol.upper()>>>",trade['symbol'].upper(), "getting symbol is >>>",symbols.upper())
                    if trade['symbol'] == symbols.upper():
                        if default_expiry:
                            # Convert string to datetime if needed
                            if isinstance(default_expiry, str):
                                try:
                                    default_expiry = datetime.fromisoformat(default_expiry)
                                except Exception as e:
                                    logger.error(f"{trade['client']} : Failed to parse expiry date: {default_expiry}. Error: {e}")
                                    default_expiry = None  # Handle as needed

                            if default_expiry:  # Ensure it's still valid after parsing
                                # Convert to IST
                                default_expiry_ist = localtime(default_expiry)

                                # Extract only the date part
                                default_expiry_date = default_expiry_ist.date()
                                # logger.info(f"default_expiry_date>>>{default_expiry_date}")

                                expiry_date = default_expiry_ist
                                default_expiry = default_expiry_ist

                                day = expiry_date.strftime("%d")
                                month = expiry_date.strftime("%b").upper()
                                year = expiry_date.strftime("%y")
                                fullyear = expiry_date.strftime("%Y")
                            else:
                                logger.error(f"{trade['client']} : Expiry date is invalid after parsing for {trade['symbol']} and user {trade['client']}. Skipping trade.")
                                order_id = 0
                                message = f"{trade['client']} : Expiry date is invalid {trade['symbol']} for user {trade['client']}. Cannot get trading symbol"
                                save_trade_order_history(
                                    LivePrice, group_service, transaction_type, trade_order_status, user, trade_symbol,
                                    order_id, status, res_data, message, strategy, Entry_type, Exit_type,
                                    Entry_price, Exit_price, EntryQty, ExitQty, webhook_signal, Exchange,
                                    Segment, Index_Symbol, order_params, broker=trade['broker']
                                )
                                continue
                        else:
                            logger.error(f"{trade['client']} : Expiry date is missing {trade['symbol']} for user {trade['client']}. Skipping trade.")
                            order_id = 0
                            message = f"{trade['client']} : Expiry date is missing {trade['symbol']} for user {trade['client']}. Cannot get trading symbol"
                            save_trade_order_history(
                                LivePrice, group_service, transaction_type, trade_order_status, user, trade_symbol,
                                order_id, status, res_data, message, strategy, Entry_type, Exit_type,
                                Entry_price, Exit_price, EntryQty, ExitQty, webhook_signal, Exchange,
                                Segment, Index_Symbol, order_params, broker=trade['broker']
                            )
                            continue
                        default_expiry=localtime(default_expiry)
                        order_params = {"symbol": trade['symbol'],"Exchange": exch_seg, "quantity": int(trade['quantity']) or default_quantity,"product_type": trade['product_type'],
                        "transaction_type":buy_sell,"price": limitPrice or 0 ,"ordertype": default_ordertype, "expiry": default_expiry,"strategy": trade['strategy']}
                        order_params = serialize_to_json(order_params)

                        # Concatenate fields to create the trading symbol
                        # skip the order and move to next user 
                        broker=trade['broker']
                        # logger.info(f"Action resolved: EntryType={Entry_type}, EntryPrice={Entry_price}, "
                        #             f"ExitType={Exit_type}, ExitPrice={Exit_price}")  
                        if not trade['product_type']:
                            message= f"trade details for client {trade['client']}: Missing  product type."
                            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message, strategy,  Entry_type,Exit_type,Entry_price,Exit_price,EntryQty,ExitQty ,webhook_signal , Exchange, Segment,Index_Symbol, order_params,broker=trade['broker'])      
                            logger.warning(f"{trade['client']} : Skipping trade for client {trade['client']}: Missing  product type")
                            continue
            
                        # Extract user-specific configurations
                        symbol = trade['symbol']
                        if symbol:
                            symbol = symbol.upper()
                        
                        # user = int(trade['client'])
                        user = User.objects.get(id = int(trade['client']))
                        strategy = trade['strategy']
                        quantity = int(trade['quantity']) or default_quantity
                        logger.info(f"{user} : quantity of trade : {quantity}")
                        product_type = trade['product_type']
                        price = limitPrice
                        ordertype = default_ordertype
                        # trade_limit = trade.trade_limit 
                        trade_limit = (int(trade['trade_limit']) or 0) * 2 
                        if not trade_limit or trade_limit==0:                           
                            message= f"Trade limit not set  for user {user}. No  trades allowed for this user symbol:{symbol}"
                            save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal , Exchange, Segment,Index_Symbol,order_params,broker=trade['broker'])
                            
                            logger.warning(f"{user} : Trade limit not set  for user {user}. No  trades allowed today.{symbol}")
                            continue
                        if trade_limit:
                            # Count user's trades for the day
                            today = datetime.today()
                            print("today>>>",today)
                            daily_trade_count = TradingLog.objects.filter(client=user, date=today ,symbol=symbol).count()
                            if daily_trade_count >= trade_limit:
                                message= f"Trade limit reached for user {user}. No more trades allowed today."
                                save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy,  Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal , Exchange, Segment,Index_Symbol,order_params,broker=trade['broker'])
                                
                                logger.warning(f"{user} : Trade limit reached for user {user}. No more trades allowed today.")
                                continue

                            logger.info(f"{user} : Placing order for user {user}. Trade count: {daily_trade_count}/{trade_limit}")
                        # if is_market_open():
                        # print("started place order market is open: transaction_type is :::::::", transaction_type ) 
                        logger.info(f"{user} : Market is open. Proceed with the trade.")
                        if transaction_type=="SELL-C_O":#Will Close the existing order and Open a new PE order
                            # print("SELL-C_O = (Close CE)SELL-C & BUY PE")
                            # First transaction: SELL-C
                            transaction_type = "SELL-C"
                            buy_sell, Type = manage_order(transaction_type, buy_sell, Type)
                            transaction_type=buy_sell
                            # if buy_sell=="BUY" and Type=="CE":
                            #     Entry_type="LE"
                            # elif buy_sell=="SELL" and  Type=="PE":
                            #     Exit_type="LX" 
                            # elif buy_sell=="SELL" and  Type=="CE":
                            #     Entry_type="LE"       
                            logger.info(f"{user} : Placing first order: Action={buy_sell}, Type={Type}")
                            trading_Symbol_sum(trade, symbols, day, month, year, Type, default_price)
                            order_response = place_order_broker(LivePrice,group_service,
                                trade, user, transaction_type, symbol, quantity, strategy, ordertype,
                                product_type, price, Lots, trade_order_status, Entry_type, Exit_type,
                                Entry_price,Exit_price,EntryQty,ExitQty, webhook_signal, Exchange, Segment, Index_Symbol,
                                triggerPrice, day, month, year,fullyear, default_price, Type, order_params
                            )
                            # if order_response:
                            print("again one order for SELL-O")
                            # Second transaction: BUY-PE
                            transaction_type = "SELL-O"
                            print("")
                            buy_sell, Type = manage_order(transaction_type, buy_sell, Type)
                            logger.info(f"{user} : Placing second order: Action={buy_sell}, Type={Type}")
                            transaction_type=buy_sell
                            order_response = place_order_broker(LivePrice,group_service,
                                trade, user, transaction_type, symbol, quantity, strategy, ordertype,
                                product_type, price, Lots, trade_order_status, Entry_type, Exit_type,
                                Entry_price,Exit_price,EntryQty,ExitQty, webhook_signal, Exchange, Segment, Index_Symbol,
                                triggerPrice, day, month, year, fullyear,default_price, Type, order_params
                            )
                        elif transaction_type=="BUY-C_O":# - Close PE & Buy CE"  BUY-C=PE CLOSE ,BUY-O = Buy CE
                            # First transaction: BUY-C
                            transaction_type = "BUY-C"
                            buy_sell, Type = manage_order(transaction_type, buy_sell, Type)
                            transaction_type=buy_sell
                            logger.info(f"{user} : Placing first order: Action={buy_sell}, Type={Type}")
                            order_response = place_order_broker(LivePrice,group_service,
                                trade, user, transaction_type, symbol, quantity, strategy, ordertype,
                                product_type, price, Lots, trade_order_status, Entry_type, Exit_type,
                                Entry_price,Exit_price,EntryQty,ExitQty, webhook_signal, Exchange, Segment, Index_Symbol,
                                triggerPrice, day, month, year,fullyear, default_price, Type, order_params
                            )
                            # if order_response:
                            print("again one order for SELL-O")
                            # Second transaction: BUY-CE
                            transaction_type = "BUY-O"
                            print("")
                            buy_sell, Type = manage_order(transaction_type, buy_sell, Type)
                            logger.info(f"{user} : Placing second order: Action={buy_sell}, Type={Type}")
                            transaction_type=buy_sell
                            order_response = place_order_broker(LivePrice,group_service,
                                trade, user, transaction_type, symbol, quantity, strategy, ordertype,
                                product_type, price, Lots, trade_order_status, Entry_type, Exit_type,
                                Entry_price,Exit_price,EntryQty,ExitQty, webhook_signal, Exchange, Segment, Index_Symbol,
                                triggerPrice, day, month, year,fullyear, default_price, Type, order_params
                            )
                        else:
                            print("signal trasaction type................",transaction_type)
                            buy_sell, Type = manage_order(transaction_type, buy_sell, Type)
                            print(f"Action: {buy_sell}, Type: {Type}")
                            transaction_type=buy_sell
                            order_response=place_order_broker(LivePrice,group_service,trade,user,transaction_type, symbol, quantity,strategy,ordertype,
                            product_type, price, Lots,trade_order_status,  Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,ExitQty,
                            webhook_signal ,Exchange, Segment,Index_Symbol,triggerPrice,day,month,year,fullyear,default_price,Type,order_params)
                                
                        # Check order response and log or handle failures
                        logger.info(f"{user} : final order repsone :::::::::::::::::::::{order_response}\n")
                        if not order_response['data']['status']:
                            order_status="Failed"
                            order_status=f"Order response failed for {trade['symbol']} with broker {trade['broker']}"
                        elif order_response['data']['status'] == "Unauthorized":
                            order_status = f"Unauthorized Order placement failed for {trade['symbol']} with broker {trade['broker']}"
                            logger.warning(order_status)  # Log the unauthorized order status
                            continue  # Skip to the next client trade if unauthorized
                        elif order_response['data']['status'] =="completed" or  order_response['data']['status'] =="complete":
                            order_status=f"Order placed successfully for {trade['symbol']} with broker {trade['broker']}"
                            TradingLog.objects.create(client=user, date=today, symbol=trade['symbol'], strategy=strategy,)
                            logger.info(f"{user} : Order placed successfully for {trade['symbol']} with broker {trade['broker']}")
                        elif order_response['data']['status']=="open":   
                            order_status=f"{user} : Order is place pending for {trade['symbol']} with broker {trade['broker']}"
                            logger.error(f"{user} : Order place is pending for {trade['symbol']} with broker {trade['broker']}") 
                        elif order_response['data']['status']=="rejected":
                            order_status=f"{user} : Order is rejected for {trade['symbol']} with broker {trade['broker']}"
                            logger.error(f"{user} : Order is rejected for {trade['symbol']} with broker {trade['broker']}")
                        elif order_response['data']['status']=="error":
                            order_status=f"{user} : Error Order placement failed for {trade['symbol']} with broker {trade['broker']}"
                        elif order_response['data']['status']=="Failed":
                            order_status=f"{user} : Order placement failed for {trade['symbol']} with broker {trade['broker']}"
                        
                        else:
                            if not order_response['data']['status']:
                                order_status="Failed"
                            order_status=f"Order placement failed for {trade['symbol']} with broker {trade['broker']}"
                        # else:
                        #     logger.info("Market is closed. Do not proceed with the trade.") 
                        #     order_status=f" can not Trade Order becouse the Market is closed. Do not proceed with the trade"
                    else:
                        order_status=f"{user} : Skipping trade for symbol {trade['symbol']} as it doesn't match the specified webhook symbol{symbols} or transaction type."
                        res_data=order_status
                        message=f"{user} : Skipping trade  for {trade['client']} : webhook trading symbol {symbols} does not match with the client trade symbol {trade['symbol']}"
                        logger.info(f"{message}")
                        # save_trade_order_history(LivePrice,group_service,transaction_type,trade_order_status,user,trade_symbol, order_id, status, res_data, message,  strategy, Entry_type,Exit_type ,Entry_price,Exit_price,EntryQty,ExitQty,webhook_signal , Exchange, Segment,Index_Symbol,order_params,broker=trade.broker)
                        # print(f"Skipping trade for symbol {trade.symbol} as it doesn't match the specified symbol and buy_sell.")
                        continue  # Skip to the next trade if the symbol and buy_sell don't match

                    if os.path.exists(csv_file):
                        with open(csv_file, mode='r', newline='') as csvfile:
                            reader = csv.DictReader(csvfile)
                            rows = list(reader)

                        # Loop through all rows and set the status_flag to 'False' for the specific client_id
                        for row in rows:
                            client_id = row['client']
                            if client_id == trade['client']:  # Check if this is the client_id to update
                                row['status_flag'] = 'False'  # Set the flag to False

                        # Write the updated data back to the CSV
                        with open(csv_file, mode='w', newline='') as csvfile:
                            fieldnames = reader.fieldnames  # Get fieldnames from the original CSV
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            
                            # Write the header
                            writer.writeheader()
                            
                            # Write all updated rows
                            writer.writerows(rows)

                        logger.info(f"Updated the status_flag to 'False' for client ID: {trade['client']}")
                    else:
                        logger.error(f"CSV file '{csv_file}' does not exist.")

                    # return Response({"status": order_status})#, status=status.HTTP_200_OK)
                    # Return success response after all iterations (if no exceptions are raised)
                except Exception as e:
                    logger.error(f"-X- ###### -X- This Order is skippe because of error: {e}")
                    logger.error(f"This trade is skipped: {trade}")
            return Response({"status":order_status}, status=200)

        except Exception as e:
            logger.error(f"Order placement encountered an error: {e}")
            return Response({"error": e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        # 🔍 **Search Filter (Client name, broker, index symbol, trading symbol)**
        search_query = request.query_params.get('q', '').strip()
        clients = clients.filter(
            Q(fullName__icontains=search_query) |
            Q(phoneNumber__icontains=search_query) | 
            Q(email__icontains=search_query)
        )


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
                # Update the broker field in ClientTradeSetting
                client_trade_settings = ClientTradeSetting.objects.filter(client=user)
                for trade_setting in client_trade_settings:
                    trade_setting.broker = broker_detail.broker_name.broker_name  # Assuming 'broker_name' is the field that links to the broker model
                    trade_setting.save()

                message = "Broker details created successfully!" if created else "Broker details updated successfully!"
                return Response({"message": message, "data": serializer.data}, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#get broker details by Admin
class AdminClientBrokerDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Retrieve broker details for the authenticated client.
        """
        client_id = kwargs.get("pk")  # Fetch client ID from URL params
        print(f"Client ID: {client_id}, Args: {args}, Kwargs: {kwargs}")

        try:
            # Fetch broker details
            broker_detail = ClientBrokerdetails.objects.filter(client_id=client_id).first()

            if not broker_detail:
                return Response(
                    {"error": "Broker details not found for the client."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Serialize the broker details
            serializer = ClientBrokerDetailsSerializer(broker_detail)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        
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
#admin can get client broker status
class AdminGetClientBrokerStatusView(APIView):
    def get(self, request, *args, **kwargs):
        client_id = kwargs.get("pk")  
        try:
            client = User.objects.get(id=client_id)
        except User.DoesNotExist:
            return Response({"error": "Client not found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch and return the broker's status
        return Response(
            {
                "id": client.id,
                "username": client.fullName,
                "email": client.email,
                "is_enable": client.is_enable,  
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
class TradeorderhistoryListView_old(APIView):
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
class ClientTradeListView_old(APIView):
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
        # broker_details = ClientBrokerdetails.objects.get(client=user, broker_name__broker_name__iexact="ZERODHA")
        kite = KiteConnect(api_key=api_key)
        # # Check if access token is valid
        # if not broker_details.access_token or broker_details.access_token_expiry < datetime.now():
        #     return JsonResponse({"error": "Access token is missing or expired. Please reauthenticate."}, status=401)
        token="h5HJ47RcoYJDsJGUGqAB7d1LEDm4Nd3F"
        # Initialize KiteConnect with API key and access token
        # kite = KiteConnect(api_key=broker_details.broker_API_UID)
        kite.set_access_token(token)
        exchange="NFO"
        symbol="BANKNIFTY25JAN48500PE"
        trading_symbol = get_trading_symbol(exchange, symbol,kite)
        # Order details
        order_params = {
            "tradingsymbol": trading_symbol,
            "exchange": "NFO",
            "transaction_type": "BUY",
            "quantity": 30,
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
    redirect_url ="https://sparks.algoview.in/callback"# "http://127.0.0.1:8000/callback-zerodha/"  # Your callback URL
    state = "zerodha"  # Optional, to track the request state

    # Construct the URL
    zerodha_url = (
            f"https://kite.zerodha.com/connect/login?api_key={api_key}&v=3"
            f"&redirect_uri={redirect_url}&state={state}"
        )
    print("zerodha_url777",zerodha_url)
    return redirect(zerodha_url)

from django.http import JsonResponse
import requests

def zerodha_callback(request):
    # Extract the request_token and state from query parameters
    request_token = "dD048whQMqDbwOL7ig1BJK21yrIl2M69"
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

# def generate_checksum(api_key, api_secret, request_token):
#     import hashlib
#     return hashlib.sha256(f"{api_key}{request_token}{api_secret}".encode()).hexdigest()
#5 Paisa -----------------

def oauth_callbacks(request):
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
#Search api for client trade

class TradeOrderHistoryFilterView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Query parameters
            service = request.query_params.get('service', None)
            strategy = request.query_params.get('strategy', None)
            trade_type = request.query_params.get('type', None)
            index_symbol = request.query_params.get('index_symbol', None)
            symbol = request.query_params.get('symbol', None)
            start_date = request.query_params.get('start_date', None)
            end_date = request.query_params.get('end_date', None)
            order_status = request.query_params.get('order_status', None)  # Entry_status or Exit_status
            broker = request.query_params.get('broker', None)
            max_lot = request.query_params.get('max_lot', None)

            # Base filters
            filters = Q()
            if service:
                filters &= Q(broker__iexact=service)
            if strategy:
                filters &= Q(strategy__iexact=strategy)
            if trade_type:
                filters &= Q(Entry_type__iexact=trade_type) | Q(Exit_type__iexact=trade_type)
            if index_symbol:
                filters &= Q(Index_Symbol__iexact=index_symbol)
            if symbol:
                filters &= Q(trading_symbol__iexact=symbol)
            if start_date and end_date:
                filters &= Q(SignalEntry_time__range=[start_date, end_date])
            if order_status:
                filters &= Q(Entry_status__iexact=order_status) | Q(Exit_status__iexact=order_status)

            # User-specific filtering
            user = request.user
            if user.role and user.role.name.lower() == 'super-admin':
                # Super-admin sees all clients' trade histories
                clients = User.objects.filter(type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.exclude(order_id=0).filter(client__in=clients).filter(filters).order_by('-id')

            elif user.role and user.role.name.lower() == 'sub-admin':
                # Sub-admin sees their assigned clients' histories
                clients = User.objects.filter(assigned_client=user, created_by=user, type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.exclude(order_id=0).filter(client__in=clients).filter(filters).order_by('-id')

            else: 
                # Regular user sees only their trade history
                trade_history = Tradeorderhistory.objects.exclude(order_id=0).filter(client=user).filter(filters).order_by('-id')

            # Pagination
            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(trade_history, request)

            # Serialization
            serializer = TradeOrderHistoryFilterSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
# #sub admin license details api
import razorpay

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET))

class CreateOrderView(APIView):

    def post(self, request):
        try:
            user = request.user
            license_qty = request.data.get("license_qty")
            license_price = request.data.get("license_price")

            if not license_qty or not license_price:
                return Response({"error": "License quantity and price are required"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate UPI ID before proceeding
        
            total_amount = int(license_qty) * int(license_price) * 100  # Convert to paise

            # Create Razorpay order
            order_data = {
                "amount": total_amount,
                "currency": "INR",
                "payment_capture": 1,
            }
            razorpay_order = razorpay_client.order.create(order_data)

            return Response({
                "status": "success",
                "message": "Order created successfully",
                "razorpay_order_id": razorpay_order["id"],
                "total_amount": total_amount // 100,
                "resp":razorpay_order
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentCallbackView(APIView):
    def get(self, request):
        try:
            order_id ="order_Pu1KH38Ka6STIt"# request.data.get("order_id")
            order_details = razorpay_client.order.fetch(order_id)
            
            # Check if payment is successful
            if order_details['status'] == 'paid':
                payment = Payment.objects.get(razorpay_order_id=order_id)
                payment.payment_status = True
                payment.save()

            return Response({"status": order_details['status'], "order_details": order_details})

        except razorpay.errors.BadRequestError:
            return Response({"error": "Invalid Order ID"}, status=400)

class VerifyPaymentAPIView(APIView):
    def post(self, request):
        data = request.data
        payment_id = data.get("razorpay_payment_id")
        order_id = data.get("razorpay_order_id")
        signature = data.get("razorpay_signature")
        payment_method = data.get("payment_method")
        upi_id = data.get("upi_id")

        payment = Payment.objects.filter(razorpay_order_id=order_id).first()

        if payment:
            payment.razorpay_payment_id = payment_id
            payment.razorpay_signature = signature
            payment.payment_method = payment_method
            payment.upi_id = upi_id if payment_method == "UPI" else None

            try:
                razorpay_client.utility.verify_payment_signature(data)
                payment.payment_status = "Completed"
                payment.save()
                return Response({"message": "Payment successful"})
            except:
                payment.payment_status = "Failed"
                payment.save()
                return Response({"message": "Payment verification failed"}, status=400)
        return Response({"message": "Order not found"}, status=404)
    

# get startegy of client for trade history filter
class StrategyListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Fetch unique strategy names from the Strategies model
            strategies = Strategies.objects.values('name').distinct()
            
            # Prepare the list of strategy names
            strategy_list = [strategy['name'] for strategy in strategies]

            # Return the list of strategies
            return Response({"strategies": strategy_list}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# for get the client strategy

class ClientStrategyListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request,*args, **kwargs):
        try:
            # Fetch unique strategy names from the Strategies model
            strategies = ClientTradeSetting.objects.values('strategy').distinct()
            
            # Prepare the list of strategy names
            strategy_list = [strategy['strategy'] for strategy in strategies]

            # Return the list of strategies
            return Response({"strategies": strategy_list}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# filter api



class TradeorderhistoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            
            # Get filters from request data
            from_date = request.GET.get('from_date', None)
            to_date = request.GET.get('to_date', None)
            strategy = request.GET.get('strategy', None)
            Index_Symbol = request.GET.get('Index_symbol', None)
            order_status = request.GET.get('order_status', None)
            broker = request.GET.get('broker', None)
            
            print(f"broker: {broker} Index_Symbol: {Index_Symbol} order_status: {order_status}")
            
            # Determine which clients to include based on user role
            if user.role and user.role.name.lower() == 'super-admin':
                clients = User.objects.filter(type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.exclude(order_id=0).exclude(order_id__isnull=True).filter(client__in=clients).order_by('-id')
            elif user.role and user.role.name.lower() == 'sub-admin':
                clients = User.objects.filter(assigned_client=user, type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.exclude(order_id=0).exclude(order_id__isnull=True).filter(client__in=clients).order_by('-id')
            else:
                trade_history = Tradeorderhistory.objects.exclude(order_id=0).exclude(order_id__isnull=True).filter(client=user).order_by('-id')

            # Dynamically apply filters based on the provided parameters
            filters = Q()

            # Apply date filter (from_date and to_date)
            if from_date:
                try:
                    from_date = datetime.strptime(from_date, "%Y-%m-%d")
                    filters &= Q(date__gte=from_date)
                except ValueError:
                    return Response({"error": "Invalid from_date format, expected YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
            
            if to_date:
                try:
                    to_date = datetime.strptime(to_date, "%Y-%m-%d")
                    filters &= Q(date__lte=to_date)
                except ValueError:
                    return Response({"error": "Invalid to_date format, expected YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

            # Apply symbol filter
            if strategy and strategy.lower() != 'all':
                filters &= Q(strategy__iexact=strategy)

            # Apply index_symbol filter
            if Index_Symbol and Index_Symbol.lower() != 'all':
                filters &= Q(Index_Symbol__iexact=Index_Symbol)

            # Apply broker filter
            if broker and broker.lower() != 'all':
                filters &= Q(broker__iexact=broker)

            # Apply order_status filter (Ensure it correctly filters)
            if order_status and order_status.lower() != 'all':
                filters &= Q(order_status__iexact=order_status)
                # trade_history = trade_history.filter(order_status=order_status)

            # 🔍 **Search Filter (Client name, broker, index symbol, trading symbol)**
            search_query = request.query_params.get('q', '').strip()
            if search_query:
                search_terms = search_query.split()  
                full_name_filters = Q()
                for term in search_terms:
                    full_name_filters |= Q(client__fullName__icontains=term)  

                filters &= (
                    full_name_filters |
                    Q(client__email__icontains=search_query) |
                    Q(broker__icontains=search_query) |
                    Q(Index_Symbol__icontains=search_query) |
                    Q(trading_symbol__icontains=search_query) |
                    Q(GroupService__icontains=search_query)
                )

            # Apply all filters
            trade_history = trade_history.filter(filters)

            # Check if trade_history is empty before pagination
            if not trade_history.exists():
                return Response({"message": "No trade history found for the given filters."}, status=status.HTTP_200_OK)

            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(trade_history, request)

            serializer = TradeorderhistorySerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TradeCompleteListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            
            # Get filters from request data
            from_date = request.GET.get('from_date', None)
            to_date = request.GET.get('to_date', None)
            strategy = request.GET.get('strategy', None)
            Index_Symbol = request.GET.get('Index_symbol', None)
            order_status = request.GET.get('order_status', None)
            broker = request.GET.get('broker', None)
            
            print(f"broker: {broker} Index_Symbol: {Index_Symbol} order_status: {order_status}")
            
            # Determine which clients to include based on user role
            if user.role and user.role.name.lower() == 'super-admin':
                clients = User.objects.filter(type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.filter(
                    client__in=clients,
                    Entry_type__isnull=False,
                    Exit_type__isnull=False,
                    order_status__in=['completed', 'complete'],
                    trade_order_status__iexact='CLOSE',
                ).filter(Q(Entry_Price__gt=0.0) | Q(Exit_Price__gt=0.0)).exclude(
                    order_id=0,
                    order_id__isnull=True,
                    EntryQty__isnull=True,
                    ExitQty__isnull=True,
                    Entry_Price__isnull=True,
                    Exit_Price__isnull=True,
                ).order_by('-id')

               
            elif user.role and user.role.name.lower() == 'sub-admin':
                clients = User.objects.filter(assigned_client=user, type_of_user='is_client', is_client=True)
                trade_history = Tradeorderhistory.objects.filter(
                    client__in=clients,
                    Entry_type__isnull=False,
                    Exit_type__isnull=False,
                    order_status__in=['completed', 'complete'],
                    trade_order_status__iexact='CLOSE',
                ).filter(Q(Entry_Price__gt=0.0) | Q(Exit_Price__gt=0.0)).exclude(
                    order_id=0,
                    order_id__isnull=True,
                    EntryQty__isnull=True,
                    ExitQty__isnull=True,
                    Entry_Price__isnull=True,
                    Exit_Price__isnull=True,
                ).order_by('-id')
            else:
                trade_history = Tradeorderhistory.objects.filter(
                    client=user,
                    Entry_type__isnull=False,
                    Exit_type__isnull=False,
                    order_status__in=['completed', 'complete'],
                    trade_order_status__iexact='CLOSE',
                ).filter(Q(Entry_Price__gt=0.0) | Q(Exit_Price__gt=0.0)).exclude(
                    order_id=0,
                    order_id__isnull=True,
                    EntryQty__isnull=True,
                    ExitQty__isnull=True,
                    Entry_Price__isnull=True,
                    Exit_Price__isnull=True,
                ).order_by('-id')
            # Dynamically apply filters based on the provided parameters
            filters = Q()

            # Apply date filter (from_date and to_date)
            if from_date:
                try:
                    from_date = datetime.strptime(from_date, "%Y-%m-%d")
                    filters &= Q(date__gte=from_date)
                except ValueError:
                    return Response({"error": "Invalid from_date format, expected YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
            
            if to_date:
                try:
                    to_date = datetime.strptime(to_date, "%Y-%m-%d")
                    filters &= Q(date__lte=to_date)
                except ValueError:
                    return Response({"error": "Invalid to_date format, expected YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

            # Apply symbol filter
            if strategy and strategy.lower() != 'all':
                filters &= Q(strategy__iexact=strategy)

            # Apply index_symbol filter
            if Index_Symbol and Index_Symbol.lower() != 'all':
                filters &= Q(Index_Symbol__iexact=Index_Symbol)

            # Apply broker filter
            if broker and broker.lower() != 'all':
                filters &= Q(broker__iexact=broker)

            # Apply order_status filter (Ensure it correctly filters)
            if order_status and order_status.lower() != 'all':
                filters &= Q(order_status__iexact=order_status)
                # trade_history = trade_history.filter(order_status=order_status)

            # 🔍 **Search Filter (Client name, broker, index symbol, trading symbol)**
            search_query = request.query_params.get('q', '').strip()
            if search_query:
                search_terms = search_query.split()  
                full_name_filters = Q()
                for term in search_terms:
                    full_name_filters |= Q(client__fullName__icontains=term)  

                filters &= (
                    full_name_filters |
                    Q(client__email__icontains=search_query) |
                    Q(broker__icontains=search_query) |
                    Q(Index_Symbol__icontains=search_query) |
                    Q(trading_symbol__icontains=search_query) |
                    Q(GroupService__icontains=search_query)
                )

            # Apply all filters
            trade_history = trade_history.filter(filters)

            # Check if trade_history is empty before pagination
            if not trade_history.exists():
                return Response({"message": "No trade history found for the given filters."}, status=status.HTTP_200_OK)

            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(trade_history, request)

            serializer = TradeorderhistorySerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ClientTradeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            
            # Get filters from request data
            from_date = request.GET.get('from_date', None)
            to_date = request.GET.get('to_date', None)
            symbol = request.GET.get('symbol', None)
            Index_Symbol = request.GET.get('Index_Symbol', None)
            order_status = request.GET.get('order_status', None)
            strategy = request.GET.get('strategy', None)
            print(f"client strategy: {strategy} symbol: {Index_Symbol}")
            
            # Determine which clients to include based on user role
            if user.role and user.role.name.lower() == 'super-admin':
                clients = User.objects.all()  # Super-admin can see all clients' trade order histories
                trade_history = Tradeorderhistory.objects.filter(client__in=clients).order_by('-id')
            elif user.role and user.role.name.lower() == 'sub-admin':
                print("Sub-Admin is called.....")
                clients = User.objects.filter(assigned_client=user)  # Sub-admin can see trade order histories of their assigned clients
                trade_history = Tradeorderhistory.objects.filter(client__in=clients).order_by('-id')
            else:
                trade_history = Tradeorderhistory.objects.filter(client=user).order_by('-id')

            # Dynamically apply filters based on the provided parameters
            filters = Q()
            search_query = request.query_params.get('q', '').strip()

            # Apply date filter (from_date and to_date)
            if from_date:
                try:
                    from_date = datetime.strptime(from_date, "%Y-%m-%d")
                    filters &= Q(date__gte=from_date)
                except ValueError:
                    return Response({"error": "Invalid from_date format, expected YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
            
            if to_date:
                try:
                    to_date = datetime.strptime(to_date, "%Y-%m-%d")
                    filters &= Q(date__lte=to_date)
                except ValueError:
                    return Response({"error": "Invalid to_date format, expected YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

            # Apply symbol filter
            if symbol and symbol.lower() != 'all':
                filters &= Q(symbol__iexact=symbol)

            # Apply order status filter
            if order_status and order_status.lower() != 'all':
                filters &= Q(order_status__iexact=order_status)

            # Apply index_symbol filter
            if Index_Symbol and Index_Symbol.lower() != 'all':
                filters &= Q(Index_Symbol__iexact=Index_Symbol)

            # Apply strategy filter
            if strategy and strategy.lower() != 'all':
                filters &= Q(strategy__iexact=strategy)

            # 🔍 **Search Filter (Client name, broker, index symbol, trading symbol)**
            if search_query:
                # Normalize the search query by trimming whitespace
                search_query = search_query.strip()
                search_terms = search_query.split()  # Split the search query into individual terms

                # Create a Q object for each term to match against the full name
                full_name_filters = Q()
                for term in search_terms:
                    full_name_filters |= Q(client__fullName__icontains=term)  # Match any part of the full name

                filters &= (
                    full_name_filters |
                    Q(client__email__icontains=search_query) |
                    Q(broker__icontains=search_query) |
                    Q(Index_Symbol__icontains=search_query) |
                    Q(trading_symbol__icontains=search_query) |
                    Q(GroupService__icontains=search_query)
                )

            # Apply all filters
            trade_history = trade_history.filter(filters)

            # Check if trade_history is empty before pagination
            if not trade_history.exists():
                return Response({"message": "No trade history found for the given filters."}, status=status.HTTP_200_OK)

            paginator = CustomPageNumberPagination()
            result_page = paginator.paginate_queryset(trade_history, request)

            serializer = TradeorderhistorySerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL)




class TradeOrderResponseDataView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, trade_id, *args, **kwargs):
        try:
            # Get the trade order by ID
            trade_order = get_object_or_404(Tradeorderhistory, id=trade_id)

            # Return response data for the specific trade order
            return Response({"response_data": trade_order.response_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
       

class IsSuperAdminOrSubAdmin(permissions.BasePermission):
    """
    Allows access only to Super Admins or Sub Admins based on role name.
    """

    def has_permission(self, request, view):
        # Allow if superuser
        if request.user.is_superuser:
            return True

        # Allow if role name is 'Sub-Admin'
        return hasattr(request.user, 'role') and getattr(request.user.role, 'name', '').lower() == 'sub-admin'
    
class BrokerLogActivityView(APIView):
    permission_classes = [IsSuperAdminOrSubAdmin]  # Only superadmin or subadmin can access

    def get(self, request, id, *args, **kwargs):
        broker_details = ClientBrokerdetails.objects.filter(client_id=id)

        if not broker_details.exists():
            return Response(
                {"detail": "No broker details found for this client."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BrokerLogSerializer(broker_details, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class UserBrokerLogActivityView(APIView):
    permission_classes = [IsAuthenticated]  # User must be logged in

    def get(self, request, user_id, *args, **kwargs):
        try:
            # Check if requesting user is accessing their own data
            if request.user.id != user_id:
                # Allow only superadmin or subadmin to access other users' logs
                if not (request.user.is_superuser or (
                    hasattr(request.user, 'role') and getattr(request.user.role, 'name', '').lower() == 'sub-admin'
                )):
                    return Response(
                        {"detail": "You do not have permission to access this user's data."},
                        status=status.HTTP_403_FORBIDDEN
                    )

            broker_details = ClientBrokerdetails.objects.filter(client_id=user_id)

            if not broker_details.exists():
                return Response(
                    {"detail": "No broker details found for this client."},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = BrokerLogSerializer(broker_details, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return Response(
                {"detail": "An error occurred while retrieving broker details."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




