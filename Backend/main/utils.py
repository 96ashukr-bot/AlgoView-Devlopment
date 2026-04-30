from django.conf import settings
from django.core.mail import get_connection
import requests
from main.models import CompanySmtpDetails

def _normalize_smtp_host(host, username=None, default_from_email=None):
    host_value = str(host or "").strip()
    sender_value = str(default_from_email or username or "").strip().lower()
    if host_value.lower() == "smtp.zoho.com" and sender_value.endswith(".in"):
        return "smtp.zoho.in"
    return host_value


def get_smtp_connection(smtp_details=None, *, open_connection=False):
    """Fetch SMTP details from the database and return an SMTP connection."""
    smtp_details = smtp_details or CompanySmtpDetails.objects.order_by("-id").first()

    try:
        # Prefer SMTP details from DB when available, otherwise fall back to
        # environment-backed Django email settings for local/dev reliability.
        email_host = _normalize_smtp_host(
            getattr(smtp_details, 'email_host', None) or settings.EMAIL_HOST,
            getattr(smtp_details, 'email_host_user', None) or settings.EMAIL_HOST_USER,
            getattr(smtp_details, 'default_from_email', None) or settings.DEFAULT_FROM_EMAIL,
        )
        email_port = getattr(smtp_details, 'email_port', None) or settings.EMAIL_PORT
        email_host_user = getattr(smtp_details, 'email_host_user', None) or settings.EMAIL_HOST_USER
        email_host_password = getattr(smtp_details, 'email_host_password', None) or settings.EMAIL_HOST_PASSWORD
        email_use_tls = getattr(smtp_details, 'email_use_tls', None)
        if email_use_tls is None:
            email_use_tls = settings.EMAIL_USE_TLS
        email_port = int(email_port)
        email_use_ssl = email_port == 465
        if email_use_ssl:
            email_use_tls = False

        # Ensure SMTP details are complete
        if not all([email_host, email_port, email_host_user, email_host_password]):
            print("Incomplete SMTP details!")
            return None

        # Create and return SMTP connection
        connection = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=email_host,
            port=email_port,
            username=email_host_user,
            password=email_host_password,
            use_tls=email_use_tls,
            use_ssl=email_use_ssl,
            timeout=20,
        )
        if open_connection:
            connection.open()
        return connection
    except Exception as e:
        print(f"Error setting up SMTP connection: {e}")
        return None


from user_agents import parse

def get_browser_info(request):
    user_agent = request.META.get('HTTP_USER_AGENT', '')  # Get User-Agent
    ua = parse(user_agent)  # Parse it using user-agents library
    browser = ua.browser.family  # Browser name (Chrome, Firefox, etc.)
    return browser
def get_client_ip(request):
    """Fetches the real client IP address, considering proxy headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    # if x_forwarded_for:
    #     ip = x_forwarded_for.split(',')[0]  # Get the first IP in the list
    # else:
    #     ip = request.META.get('REMOTE_ADDR')  # Direct IP
    ip=requests.get('https://api.ipify.org').text     
    print("ip>>",ip)    
    return ip

from django.utils import timezone

from datetime import datetime
import pytz

def get_login_time():
    """Returns the current time in IST (Indian Standard Time)."""
    ist = pytz.timezone('Asia/Kolkata')  # Indian Timezone
    ist_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')  # Format YYYY-MM-DD HH:MM:SS

    return ist_time
