
from main.models import *
from rest_framework.views import APIView
from main.serializers import *
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from main.serializers import CompanyProfileSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from main.models import CompanyProfileDetails
from main.serializers import CompanyProfileSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from main.models import CompanyProfileDetails
from main.serializers import *
class CompanyProfileDetailsView(APIView):
    # GET request to fetch all company profile details
    def get(self, request):
        companies = CompanyProfileDetails.objects.all()
        serializer = CompanyProfileDetailsSerializer(companies, many=True)
        return Response(serializer.data)
    
    # POST request to create a new company profile
    def post(self, request):
        serializer = CompanyProfileDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Save the new company profile
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CompanyProfileDetailView(APIView):

    def get(self, request, *args, **kwargs):
        """Retrieve a single company by ID or all companies if no ID is provided."""
        try:
            company_id = kwargs.get('pk')
            if company_id:
                company = CompanyProfileDetails.objects.get(pk=company_id)
                serializer = CompanyProfileSerializer(company)
                return Response(
                    {"status": "success", "message": "Company retrieved successfully.", "data": serializer.data},
                    status=status.HTTP_200_OK
                )
            else:
                companies = CompanyProfileDetails.objects.all()
                serializer = CompanyProfileSerializer(companies, many=True)
                return Response(
                    {"status": "success", "message": "Companies retrieved successfully.", "data": serializer.data},
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

    def post(self, request, *args, **kwargs):
        try:
            # Ensure that we receive the image as part of the request
            serializer = CompanyProfileSerializer(data=request.data)
            if serializer.is_valid():
                # Save the company profile with the logo (if provided)
                serializer.save()
                return Response({
                    "status": "success",
                    "message": "Company created successfully.",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                "status": "failed",
                "message": "Validation error.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                "status": "error",
                "message": "An unexpected error occurred.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def put(self, request, *args, **kwargs):
        """Update an existing company."""
        try:
            company = CompanyProfileDetails.objects.get(pk=kwargs.get('pk'))
            serializer = CompanyProfileSerializer(company, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"status": "success", "message": "Company details updated successfully.", "data": serializer.data},
                    status=status.HTTP_200_OK
                )
            return Response(
                {"status": "failed", "message": "Validation error.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        except CompanyProfileDetails.DoesNotExist:
            return Response(
                {"status": "failed", "message": "Company not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, *args, **kwargs):
        """Delete a company by ID."""
        try:
            company = CompanyProfileDetails.objects.get(pk=kwargs.get('pk'))
            company.delete()
            return Response(
                {"status": "success", "message": "Company deleted successfully."},
                status=status.HTTP_200_OK
            )
        except CompanyProfileDetails.DoesNotExist:
            return Response(
                {"status": "failed", "message": "Company not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CompanySmtpDetailView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            serializer = CompanySmtpDetailsSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": "success",
                    "message": "SMTP configuration created successfully.",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({
                "status": "failed",
                "message": "Validation error.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def get(self, request, *args, **kwargs):
        try:
            smtp_id = kwargs.get('pk')
            smtp_details = CompanySmtpDetails.objects.get(pk=smtp_id)
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
            
    def put(self, request, *args, **kwargs):
        try:
            smtp_id = kwargs.get('pk')
            smtp_details = CompanySmtpDetails.objects.get(pk=smtp_id)
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

    def delete(self, request, *args, **kwargs):
        try:
            smtp_id = kwargs.get('pk')
            smtp_details = CompanySmtpDetails.objects.get(pk=smtp_id)
            smtp_details.delete()
            return Response({
                "status": "success",
                "message": "SMTP configuration deleted successfully."
            }, status=status.HTTP_204_NO_CONTENT)
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

    