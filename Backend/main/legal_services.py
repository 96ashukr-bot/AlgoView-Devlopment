import logging
import os
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone

from main.models import ClientAgreementAcceptance, LegalAgreement, calculate_terms_hash

logger = logging.getLogger(__name__)

DEFAULT_AGREEMENT_CONTENT_FILE = os.path.join(
    os.path.dirname(__file__),
    "legal_agreements",
    "software_development_automation_services_v1.txt",
)


def get_client_snapshot(user):
    full_name = (getattr(user, "fullName", "") or "").strip()
    if not full_name:
        full_name = f"{getattr(user, 'firstName', '') or ''} {getattr(user, 'lastName', '') or ''}".strip()
    return {
        "client_name": full_name or str(getattr(user, "email", "") or user.id),
        "client_email": getattr(user, "email", "") or "",
        "client_mobile": getattr(user, "phoneNumber", "") or "",
    }


def get_request_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def get_active_agreement():
    return LegalAgreement.objects.filter(is_active=True).order_by("-created_at", "-id").first()


def client_has_accepted_active_agreement(user):
    agreement = get_active_agreement()
    if not agreement:
        return True
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return ClientAgreementAcceptance.objects.filter(
        client=user,
        agreement=agreement,
        terms_version_hash=agreement.content_hash,
    ).exists()


def render_agreement_content(agreement, client_snapshot=None, accepted_at=None, ip_address=None):
    content = agreement.content if agreement else ""
    snapshot = client_snapshot or {}
    rendered_date = timezone.localtime(accepted_at).strftime("%d / %m / %Y") if accepted_at else timezone.localtime().strftime("%d / %m / %Y")
    rendered_datetime = timezone.localtime(accepted_at).strftime("%d-%m-%Y %H:%M:%S") if accepted_at else timezone.localtime().strftime("%d-%m-%Y %H:%M:%S")
    client_name = snapshot.get("client_name") or ""
    client_mobile = snapshot.get("client_mobile") or ""
    client_email = snapshot.get("client_email") or ""
    replacements = {
        'This Software Development and Automation Services Agreement ("Agreement") is entered into on ___ / ___ / ______ between:':
            f'This Software Development and Automation Services Agreement ("Agreement") is entered into on {rendered_date} between:',
        "**Client Name:** ___________________________________": f"**Client Name:** {client_name}",
        "**Mobile Number:** ________________________________": f"**Mobile Number:** {client_mobile}",
        "**Email Address:** _________________________________": f"**Email Address:** {client_email}",
        "Name: ______________________________________": f"Name: {client_name}",
        "Date: ______________________________________": f"Date: {rendered_datetime}",
    }
    for source, target in replacements.items():
        content = content.replace(source, target)
    if ip_address:
        content = f"{content}\n\nAccepted IP Address: {ip_address}"
    return content


def _draw_wrapped_text(canvas, text, x, y, width, font_name="Helvetica", font_size=10, line_gap=4):
    from reportlab.lib.units import inch
    from reportlab.pdfbase.pdfmetrics import stringWidth

    canvas.setFont(font_name, font_size)
    usable_width = width
    line_height = font_size + line_gap
    for paragraph in str(text or "").splitlines() or [""]:
        words = paragraph.split(" ")
        line = ""
        if not words:
            y -= line_height
            continue
        for word in words:
            candidate = f"{line} {word}".strip()
            if stringWidth(candidate, font_name, font_size) <= usable_width:
                line = candidate
                continue
            canvas.drawString(x, y, line)
            y -= line_height
            line = word
            if y < inch:
                canvas.showPage()
                y = 10.5 * inch
                canvas.setFont(font_name, font_size)
        canvas.drawString(x, y, line)
        y -= line_height
    return y


def generate_acceptance_pdf(acceptance):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 0.65 * inch
    y = height - margin

    pdf.setTitle(f"{acceptance.agreement.title} {acceptance.agreement_version}")
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(margin, y, acceptance.agreement.title)
    y -= 22
    pdf.setFont("Helvetica", 10)
    pdf.drawString(margin, y, f"Version: {acceptance.agreement_version}")
    y -= 14
    pdf.drawString(margin, y, f"Terms Version Hash: {acceptance.terms_version_hash}")
    y -= 28
    rendered_content = render_agreement_content(
        acceptance.agreement,
        {
            "client_name": acceptance.client_name,
            "client_mobile": acceptance.client_mobile,
            "client_email": acceptance.client_email,
        },
        accepted_at=acceptance.accepted_at,
        ip_address=acceptance.ip_address,
    )
    y = _draw_wrapped_text(pdf, rendered_content, margin, y, width - (2 * margin), font_size=10)

    pdf.showPage()
    y = height - margin
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(margin, y, "AGREEMENT ACCEPTANCE CERTIFICATE")
    y -= 32

    certificate_rows = [
        ("Company", "Sparkbridge Innovations"),
        ("Client Name", acceptance.client_name),
        ("Email", acceptance.client_email),
        ("Mobile", acceptance.client_mobile),
        ("Agreement Title", acceptance.agreement.title),
        ("Agreement Version", acceptance.agreement_version),
        ("Terms Version Hash", acceptance.terms_version_hash),
        ("Accepted Date & Time", timezone.localtime(acceptance.accepted_at).strftime("%d-%m-%Y %H:%M:%S")),
        ("IP Address", acceptance.ip_address or ""),
        ("User Agent", acceptance.user_agent or ""),
    ]
    for label, value in certificate_rows:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(margin, y, f"{label}:")
        y -= 14
        y = _draw_wrapped_text(pdf, value, margin + 18, y, width - (2 * margin) - 18, font_size=10)
        y -= 5

    declaration = (
        "I hereby confirm that I have read, understood, and accepted the Software "
        "Development and Automation Services Agreement, No Refund Policy, Risk "
        "Disclaimer, and all associated terms and conditions provided by Sparkbridge "
        "Innovations.\n\nThis agreement was electronically accepted through the "
        "Sparkbridge software platform."
    )
    y -= 8
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(margin, y, "Declaration:")
    y -= 18
    _draw_wrapped_text(pdf, declaration, margin, y, width - (2 * margin), font_size=10)

    pdf.save()
    buffer.seek(0)
    filename = f"sparkbridge-agreement-{acceptance.client_id}-{acceptance.agreement_version}.pdf"
    acceptance.pdf_file.save(filename, ContentFile(buffer.read()), save=False)
    acceptance.pdf_generated_at = timezone.now()
    acceptance.status = ClientAgreementAcceptance.STATUS_PDF_GENERATED
    acceptance.email_status = ClientAgreementAcceptance.STATUS_PDF_GENERATED
    acceptance.save(update_fields=["pdf_file", "pdf_generated_at", "status", "email_status"])
    return acceptance.pdf_file


def send_acceptance_emails(acceptance, send_client=True, send_admin=True):
    admin_email = getattr(settings, "AGREEMENT_ADMIN_EMAIL", "") or getattr(settings, "DEFAULT_FROM_EMAIL", "")
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    accepted_at = timezone.localtime(acceptance.accepted_at).strftime("%d-%m-%Y %H:%M:%S")
    failures = []

    if not acceptance.pdf_file:
        generate_acceptance_pdf(acceptance)

    if send_client and acceptance.client_email:
        try:
            client_message = EmailMessage(
                subject="Your Accepted Software Development Agreement - Sparkbridge Innovations",
                body=(
                    f"Dear {acceptance.client_name},\n\n"
                    "Attached is a copy of the Software Development and Automation Services Agreement "
                    f"accepted by you on {accepted_at}.\n\n"
                    f"Terms Version Hash: {acceptance.terms_version_hash}\n\n"
                    "Please keep this copy for your records.\n\n"
                    "Regards,\nSparkbridge Innovations"
                ),
                from_email=from_email,
                to=[acceptance.client_email],
            )
            client_message.attach_file(acceptance.pdf_file.path)
            client_message.send(fail_silently=False)
            acceptance.client_email_sent_at = timezone.now()
        except Exception as exc:
            logger.exception("Client agreement email failed for acceptance %s", acceptance.id)
            failures.append(str(exc))

    if send_admin and admin_email:
        try:
            admin_message = EmailMessage(
                subject=f"Client Agreement Accepted - {acceptance.client_name}",
                body=(
                    "Client has accepted agreement.\n\n"
                    f"Client Name:\n{acceptance.client_name}\n\n"
                    f"Email:\n{acceptance.client_email}\n\n"
                    f"Mobile:\n{acceptance.client_mobile}\n\n"
                    f"Agreement Version:\n{acceptance.agreement_version}\n\n"
                    f"Terms Hash:\n{acceptance.terms_version_hash}\n\n"
                    f"Accepted Date:\n{accepted_at}\n\n"
                    f"IP Address:\n{acceptance.ip_address}\n\n"
                    "PDF attached."
                ),
                from_email=from_email,
                to=[admin_email],
            )
            admin_message.attach_file(acceptance.pdf_file.path)
            admin_message.send(fail_silently=False)
            acceptance.admin_email_sent_at = timezone.now()
        except Exception as exc:
            logger.exception("Admin agreement email failed for acceptance %s", acceptance.id)
            failures.append(str(exc))

    acceptance.email_status = (
        ClientAgreementAcceptance.STATUS_EMAIL_FAILED if failures else ClientAgreementAcceptance.STATUS_EMAIL_SENT
    )
    acceptance.status = acceptance.email_status
    acceptance.save(update_fields=["client_email_sent_at", "admin_email_sent_at", "email_status", "status"])
    return failures


@transaction.atomic
def accept_current_agreement(user, request):
    agreement = get_active_agreement()
    if not agreement:
        raise ValueError("No active legal agreement is configured.")

    snapshot = get_client_snapshot(user)
    acceptance, created = ClientAgreementAcceptance.objects.get_or_create(
        client=user,
        agreement=agreement,
        defaults={
            "agreement_version": agreement.version,
            "terms_version_hash": calculate_terms_hash(agreement.content, agreement.version),
            "ip_address": get_request_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            **snapshot,
        },
    )
    if not created:
        return acceptance, False, []

    generate_acceptance_pdf(acceptance)
    email_failures = send_acceptance_emails(acceptance)
    return acceptance, True, email_failures


def seed_agreement_from_file(content_file=None, version="v1.0", created_by=None):
    content_file = content_file or DEFAULT_AGREEMENT_CONTENT_FILE
    if not content_file or not os.path.exists(content_file):
        raise FileNotFoundError("Master agreement content file is required and was not found.")
    with open(content_file, "r", encoding="utf-8") as handle:
        content = handle.read().strip()
    if not content:
        raise ValueError("Master agreement content file is empty.")

    with transaction.atomic():
        LegalAgreement.objects.filter(is_active=True).update(is_active=False)
        agreement, created = LegalAgreement.objects.get_or_create(
            version=version,
            defaults={
                "title": "Software Development and Automation Services Agreement",
                "content": content,
                "is_active": True,
                "created_by": created_by,
            },
        )
        if not created:
            agreement.is_active = True
            agreement.save(update_fields=["is_active", "updated_at"])
        return agreement, created
