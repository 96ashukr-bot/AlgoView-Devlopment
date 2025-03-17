
from main.models import *
from rest_framework.views import APIView
from main.serializers import *
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from main.serializers import *#CompanyProfileSerializer
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import now, timedelta
from .models import WebsocketDetails

class WebsocketTokenView(APIView):
    def get(self, request, *args, **kwargs):
        """Retrieve the latest valid token or mark expired ones."""
        token = WebsocketDetails.objects.order_by("-id").first()

        if token:
            # Check and update the token status
            if token.expiry_time and now() > token.expiry_time:
                token.token_status = "inactive"
                token.save()

            return Response(
                {
                    "status": "success" if token.token_status == "active" else "failed",
                    "auth_token": token.Auth_token,
                    "token_status": token.token_status,
                },
                status=status.HTTP_200_OK #if token.token_status == "active" else status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"status": "failed", "message": "No token found."},
            status=status.HTTP_404_NOT_FOUND,
        )


    def put(self, request, *args, **kwargs):
        """Update the token or create a new one, and set expiry time."""
        data = request.data
        auth_token = data.get("auth_token")

        if not auth_token:
            return Response(
                {"status": "failed", "message": "Auth token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create or update the latest token
        token, created = WebsocketDetails.objects.update_or_create(
            id=WebsocketDetails.objects.order_by("-id").first().id
            if WebsocketDetails.objects.exists()
            else None,
            defaults={"Auth_token": auth_token, "token_status": "active"},
        )

        # Set expiry for **next day's** 3:30 AM
        now_time = now()
        if now_time.hour < 3 or (now_time.hour == 3 and now_time.minute < 30):
            # It's before 3:30 AM today, so expire today at 3:30 AM
            expiry_date = now_time.date()
        else:
            # It's after 3:30 AM, so expire tomorrow at 3:30 AM
            expiry_date = now_time.date() + timedelta(days=1)

        token.expiry_time = datetime.combine(expiry_date, datetime.min.time()) + timedelta(
            hours=3, minutes=30
        )
        token.save()

        return Response(
            {
                "status": "success",
                "message": "Token updated successfully." if not created else "New token created.",
                "data": {"auth_token": token.Auth_token, "token_status": token.token_status},
            },
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED,
        )
class WebsocketTokenViewww(APIView):
    def get(self, request, *args, **kwargs):
        """Retrieve the latest valid token from the database."""
        token = WebsocketDetails.objects.order_by("-id").first()

        if token and token.token_status not in ["inactive", "not valid"]:
            return Response(
                {"status": "success", "auth_token": token.Auth_token, "token_status": token.token_status},
                status=status.HTTP_200_OK
            )
        return Response(
            {"status": "failed", "message": "No valid token found."},
            status=status.HTTP_404_NOT_FOUND
        )

    def put(self, request, *args, **kwargs):
        """Update or create the token when it's expired or unauthorized."""
        data = request.data
        auth_token = data.get("auth_token")
     
        if not auth_token:
            return Response(
                {"status": "failed", "message": "Auth token is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update if exists or create a new entry if not also updtae token status 
        token, created = WebsocketDetails.objects.update_or_create(
            id=WebsocketDetails.objects.order_by("-id").first().id if WebsocketDetails.objects.exists() else None,
            defaults={"Auth_token": auth_token, "token_status": token_status},
        )
        # Calculate Expiry Time (Fixed at 3:30 AM the Next Day)
        now_time = now()
        expiry_date = now_time.date() if now_time.hour < 3 or (now_time.hour == 3 and now_time.minute < 30) else now_time.date() + timedelta(days=1)
        expiry_time = datetime.combine(expiry_date, datetime.min.time()) + timedelta(hours=3, minutes=30)
        print("expiry_time>>>>",expiry_time)
        token_status=WebsocketDetails.save()

        return Response(
            {
                "status": "success",
                "message": "Token updated successfully." if not created else "New token created.",
                "data": {"auth_token": token.Auth_token, "token_status": token.token_status},
            },
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED
        )

class CompanyProfileDetailView(APIView):

    def get(self, request, *args, **kwargs):
        user=request.user
        """Retrieve a single company by ID or all companies if no ID is provided."""
        try:

            company = CompanyProfileDetails.objects.get(user=user)
            serializer = CompanyProfileSerializer(company)
            return Response(
                {"status": "success", "message": "Company retrieved successfully.", "data": serializer.data},
                status=status.HTTP_200_OK
            )

        except CompanyProfileDetails.DoesNotExist:
            return Response(
                {"status": "failed", "message": "Company not found.", "data": None},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": "An unexpected error occurred.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class CompanyProfileUpdateView(APIView):            
    def put(self, request, *args, **kwargs):
        """
        Retrieve or create the company profile for the authenticated user.
        If it exists, update the provided fields.
        """
        user = request.user

        # Retrieve or create a company profile for the user
        company, created = CompanyProfileDetails.objects.get_or_create(user=user)

        serializer = CompanyProfileSerializer(company, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            message = "Company profile created successfully." if created else "Company details updated successfully."
            return Response(
                {"status": "success", "message": message, "data": serializer.data},
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )

        return Response(
            {"status": "failed", "message": "Validation error.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    
class CompanySmtpDetailView(APIView):    
    def get(self, request, *args, **kwargs):
        try:
            user=request.user
            smtp_details = CompanySmtpDetails.objects.get(user=user)
            serializer = CompanySmtpDetailsSerializer(smtp_details)
            return Response({
                "status": "success",
                "message": "SMTP configuration retrieved successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except CompanySmtpDetails.DoesNotExist:
            return Response({
                "status": "failed",
                "message": "SMTP configuration not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class CompanySmtpUpdateView(APIView):             
    def put(self, request, *args, **kwargs):
        try:
            user=request.user
            smtp_details, created = CompanySmtpDetails.objects.get_or_create(user=user)
            serializer = CompanySmtpSerializer(smtp_details, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": "success",
                    "message": "SMTP configuration updated successfully.",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            return Response({
                "status": "failed",
                "message": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except CompanySmtpDetails.DoesNotExist:
            return Response({
                "status": "failed",
                "message": "SMTP configuration not found."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   