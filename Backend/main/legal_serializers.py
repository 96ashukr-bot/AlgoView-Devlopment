from rest_framework import serializers

from main.models import ClientAgreementAcceptance, LegalAgreement


class LegalAgreementSerializer(serializers.ModelSerializer):
    hash = serializers.CharField(source="content_hash", read_only=True)

    class Meta:
        model = LegalAgreement
        fields = ["id", "title", "version", "content", "hash", "is_active", "created_at"]


class ClientAgreementAcceptanceSerializer(serializers.ModelSerializer):
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = ClientAgreementAcceptance
        fields = [
            "id",
            "client_id",
            "client_name",
            "client_email",
            "client_mobile",
            "agreement_version",
            "terms_version_hash",
            "accepted_at",
            "ip_address",
            "user_agent",
            "pdf_url",
            "pdf_generated_at",
            "client_email_sent_at",
            "admin_email_sent_at",
            "email_status",
            "status",
            "created_at",
        ]

    def get_pdf_url(self, obj):
        if not obj.pdf_file:
            return None
        request = self.context.get("request")
        url = obj.pdf_file.url
        return request.build_absolute_uri(url) if request else url
