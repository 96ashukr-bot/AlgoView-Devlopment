from django.core.mail import get_connection
from main.models import CompanySmtpDetails

def get_smtp_connection():
    """Fetch SMTP details from the database and return an SMTP connection."""
    smtp_details = CompanySmtpDetails.objects.first()

    if not smtp_details:
        print("SMTP details not found!")
        return None

    try:
        # Fetch SMTP details from DB
        email_host = smtp_details.email_host
        email_port = smtp_details.email_port
        email_host_user = smtp_details.email_host_user
        email_host_password = smtp_details.email_host_password  
        email_use_tls = smtp_details.email_use_tls
        default_from_email = smtp_details.default_from_email

        # print(f"Email Host: {email_host}, Port: {email_port}, User: {email_host_user}")

        # Ensure SMTP details are complete
        if not all([email_host, email_port, email_host_user, email_host_password]):
            print("Incomplete SMTP details!")
            return None

        # Create and return SMTP connection
        return get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=email_host,
            port=email_port,
            username=email_host_user,
            password=email_host_password,
            use_tls=email_use_tls,
        )
    except Exception as e:
        print(f"Error setting up SMTP connection: {e}")
        return None
