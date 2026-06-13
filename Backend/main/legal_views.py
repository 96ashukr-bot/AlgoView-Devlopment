from django.http import FileResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.legal_serializers import ClientAgreementAcceptanceSerializer, LegalAgreementSerializer
from main.legal_services import (
    accept_current_agreement,
    client_has_accepted_active_agreement,
    get_active_agreement,
    get_client_snapshot,
    render_agreement_content,
    send_acceptance_emails,
)
from main.models import ClientAgreementAcceptance
from main.permissions import can_access_client_record, is_end_user, is_platform_admin, is_subadmin_user


class LegalAcceptancePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 150
    page_query_param = "page_number"


class CurrentAgreementAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        agreement = get_active_agreement()
        if not agreement:
            return Response({"detail": "No active legal agreement is configured."}, status=status.HTTP_404_NOT_FOUND)
        client = get_client_snapshot(request.user)
        agreement_data = LegalAgreementSerializer(agreement).data
        agreement_data["content"] = render_agreement_content(agreement, client)
        return Response(
            {
                "agreement": agreement_data,
                "version": agreement.version,
                "hash": agreement.content_hash,
                "client": client,
            },
            status=status.HTTP_200_OK,
        )


class MyAcceptanceStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_end_user(request.user):
            return Response({"accepted": True, "agreement_version": None, "hash": None}, status=status.HTTP_200_OK)
        agreement = get_active_agreement()
        if not agreement:
            return Response({"accepted": True, "agreement_version": None, "hash": None}, status=status.HTTP_200_OK)
        accepted = client_has_accepted_active_agreement(request.user)
        acceptance = None
        if accepted:
            acceptance = ClientAgreementAcceptance.objects.filter(client=request.user, agreement=agreement).first()
        return Response(
            {
                "accepted": accepted,
                "agreement_version": agreement.version,
                "hash": agreement.content_hash,
                "accepted_at": acceptance.accepted_at if acceptance else None,
            },
            status=status.HTTP_200_OK,
        )


class AcceptAgreementAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not is_end_user(request.user):
            return Response({"detail": "Agreement acceptance is required only for client users."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            acceptance, created, email_failures = accept_current_agreement(request.user, request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ClientAgreementAcceptanceSerializer(acceptance, context={"request": request})
        return Response(
            {
                "accepted": True,
                "created": created,
                "email_status": acceptance.email_status,
                "email_failures": email_failures,
                "acceptance": serializer.data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class MyAgreementPDFAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        agreement = get_active_agreement()
        acceptance = (
            ClientAgreementAcceptance.objects.filter(client=request.user, agreement=agreement).order_by("-accepted_at", "-id").first()
            if agreement
            else ClientAgreementAcceptance.objects.filter(client=request.user).order_by("-accepted_at", "-id").first()
        )
        if not acceptance or not acceptance.pdf_file:
            return Response({"detail": "Agreement PDF not found."}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(open(acceptance.pdf_file.path, "rb"), content_type="application/pdf", as_attachment=True)


class LegalAcceptanceListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if is_platform_admin(request.user):
            queryset = ClientAgreementAcceptance.objects.select_related("client", "agreement").all()
        elif is_subadmin_user(request.user):
            queryset = ClientAgreementAcceptance.objects.select_related("client", "agreement").filter(client__assigned_client=request.user)
        else:
            queryset = ClientAgreementAcceptance.objects.select_related("client", "agreement").filter(client=request.user)

        search = (request.GET.get("search") or "").strip()
        if search:
            queryset = queryset.filter(Q(client_name__icontains=search) | Q(client_email__icontains=search))

        paginator = LegalAcceptancePagination()
        page = paginator.paginate_queryset(queryset.order_by("-accepted_at", "-id"), request)
        serializer = ClientAgreementAcceptanceSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class LegalAcceptancePDFDownloadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acceptance_id):
        acceptance = get_object_or_404(ClientAgreementAcceptance, id=acceptance_id)
        if not is_platform_admin(request.user) and not can_access_client_record(request.user, acceptance.client):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        if not acceptance.pdf_file:
            return Response({"detail": "Agreement PDF not found."}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(open(acceptance.pdf_file.path, "rb"), content_type="application/pdf", as_attachment=True)


class LegalAcceptanceResendEmailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acceptance_id):
        if not is_platform_admin(request.user):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        acceptance = get_object_or_404(ClientAgreementAcceptance, id=acceptance_id)
        target = (request.data.get("target") or "both").strip().lower()
        failures = send_acceptance_emails(
            acceptance,
            send_client=target in {"client", "both"},
            send_admin=target in {"admin", "both"},
        )
        serializer = ClientAgreementAcceptanceSerializer(acceptance, context={"request": request})
        return Response({"email_status": acceptance.email_status, "failures": failures, "acceptance": serializer.data})
