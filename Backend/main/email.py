from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags
from main.models import *
from main.companysmtpsetails import get_company_profile,get_smtp_details
from main.utils import get_smtp_connection
import logging

logger = logging.getLogger(__name__)
company_profile = get_company_profile()
smtp_details = get_smtp_details()

# from main.companysmtpsetails import smtp_details,company_profile
company_profile=company_profile if company_profile else None
# Safely access the fields, ensuring company_profile is not None
support_email = company_profile.company_support_email if company_profile else None
contact_number = company_profile.company_phone_number if company_profile else None
company_logo = company_profile.company_logo if company_profile else None
company_sender_name=company_profile.company_sender_name if company_profile else None
# Access settings for static values
login_link = company_profile.login_link if company_profile else None
help_center_link = company_profile.help_center_link if company_profile else None
company_website =company_profile.company_website if company_profile else None

smtp_details=smtp_details
default_from_email=smtp_details.email_host_user if smtp_details else   "no-reply@example.com" 
def _get_email_context_defaults():
    company_profile = get_company_profile()
    smtp_details = get_smtp_details()
    support_email = getattr(company_profile, 'company_support_email', None) or settings.DEFAULT_FROM_EMAIL
    contact_number = getattr(company_profile, 'company_phone_number', None)
    company_sender_name = getattr(company_profile, 'company_sender_name', None) or "AlgoView"
    login_link = getattr(company_profile, 'login_link', None) or "https://www.admin.algoview.in/login"
    help_center_link = getattr(company_profile, 'help_center_link', None) or login_link
    company_website = getattr(company_profile, 'company_website', None) or "https://example.com"
    from_email = (
        getattr(smtp_details, 'default_from_email', None)
        or getattr(smtp_details, 'email_host_user', None)
        or settings.DEFAULT_FROM_EMAIL
    )
    return {
        'support_email': support_email,
        'contact_number': contact_number,
        'company_sender_name': company_sender_name,
        'login_link': login_link,
        'help_center_link': help_center_link,
        'company_website': company_website,
        'from_email': from_email,
    }

class EmailServicesss:
    
    @staticmethod
    def send_password_email(email, password, user_name, login_link, support_email, help_center_link, company_website, contact_number):
            subject = 'Welcome to AlgoView Technologies! Your Registration is Complete'
            message = f"""
            Dear {user_name},

            Thank you for registering with AlgoView Technologies! Your account has been successfully created, and you are now part of our community.

            To help you get started, here is your default password and a link to proceed with your first login:
            
            Default Password: {password}
            Login Link: {login_link}
            
            We recommend changing your password after your first login for enhanced security. You can update your password by navigating to the settings section within your dashboard.

            What’s next?
            - Click the login link above to sign into your account.
            - After logging in, take a moment to explore the platform and familiarize yourself with our features.
            - If you need assistance, feel free to reach out to our support team at {support_email}.

            Need help?
            For any questions or support, don’t hesitate to contact us at {support_email} or visit our help center: {help_center_link}.

            We’re excited to have you on board and look forward to supporting your journey with us!

            Best regards,
            The AlgoView Technologies Team
            {company_website}
            {support_email} | {contact_number}
            """
            from_email = default_from_email
            send_mail(subject, message, from_email, [email])
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

class EmailService:
    
    @staticmethod
    def send_password_email(email, password, user_name, login_link, support_email, help_center_link, company_website, contact_number):
        smtp_connection = get_smtp_connection()
        if not smtp_connection:
            raise RuntimeError("SMTP connection could not be established.")

        defaults = _get_email_context_defaults()
        subject = 'Welcome to AlgoView Technologies! Your Registration is Complete'
        # Render the HTML template with context data
        context = {
            'user_name': user_name,
            'password': password,
            'login_link': login_link or defaults['login_link'],
            'support_email': support_email or defaults['support_email'],
            'help_center': help_center_link or defaults['help_center_link'],
            'company_website': company_website or defaults['company_website'],
            'contact_number': contact_number or defaults['contact_number']
        }
        html_message = render_to_string('welcome_email.html', context)

        # Create the email
        email_message = EmailMultiAlternatives(
            subject,
            "",
            f"{defaults['company_sender_name']} <{defaults['from_email']}>",
            [email],
            connection=smtp_connection,
        )
        email_message.attach_alternative(html_message, "text/html")  # Attach the HTML version

        # Send the email
        email_message.send()
        
    @staticmethod
    def send_login_email_otp(email, otp_code, user_name):
        smtp_connection = get_smtp_connection()
        if not smtp_connection:
            raise RuntimeError("SMTP connection could not be established.")

        defaults = _get_email_context_defaults()
        subject='Your Login OTP for AlgoView Technologies'
        # Define the context for the email template
        context = {
            'user_name': user_name,           # User's name
            'otp_code': otp_code,             # One-Time Password
            'valid_for_minutes': 2,  # OTP expiration time
            'support_email': defaults['support_email'],
            'company_website': defaults['company_website'],
            'help_center': defaults['help_center_link'],
            'contact_number': defaults['contact_number'],
        }

        # Render the HTML email template
        html_message = render_to_string('login_email.html', context)
        email_message = EmailMultiAlternatives(
            subject,
            "",
            f"{defaults['company_sender_name']} <{defaults['from_email']}>",
            [email],
            connection=smtp_connection,
        )
        email_message.attach_alternative(html_message, "text/html")  # Attach the HTML version

        # Send the email
        email_message.send()
  
