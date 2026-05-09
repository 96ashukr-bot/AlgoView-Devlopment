# # users/tasks.py
# from celery import shared_task
# from django.core.mail import send_mail
# from django.conf import settings

# @shared_task
# def send_password_email(email, password):
#     subject = 'Your account has been created'
#     message = f'Your account has been created. Your password is: {password}'
#     from_email = settings.DEFAULT_FROM_EMAIL
#     send_mail(subject, message, from_email, [email])
# tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging
logger = logging.getLogger('main')

from main.models import *
from main.utils import get_smtp_connection
from django.templatetags.static import static
    # Get company profile for support email and website
# company_profile = CompanyProfileDetails.objects.first()
from main.companysmtpsetails import get_company_profile,get_smtp_details
company_profile = get_company_profile()
smtp_details = get_smtp_details()


@shared_task(bind=True, autoretry_for=(), max_retries=0)
def route_execution_order_task(self, *, client_id, broker_details_id, order_payload, correlation_id=None):
    """Proxy-safe order execution task; all broker egress stays inside the router."""
    from main.models import ClientBrokerdetails, User
    from main.services.execution_router import route_order_to_execution_node

    client = User.objects.get(pk=client_id)
    broker_details = ClientBrokerdetails.objects.select_related("execution_node", "broker_name").get(
        pk=broker_details_id,
        client=client,
    )
    payload = dict(order_payload or {})
    if correlation_id:
        payload.setdefault("correlation_id", correlation_id)
        payload.setdefault("idempotency_key", correlation_id)
    return route_order_to_execution_node(client, broker_details, payload)

company_profile=company_profile if company_profile else None

support_email = company_profile.company_support_email if company_profile else "support@example.com"
company_website = company_profile.company_website if company_profile else "https://example.com"
logo_url = company_profile.company_logo if company_profile else "https://example.com/logo.png"
login_link = company_profile.login_link if company_profile else "https://www.admin.algoview.in/login"
help_center_link = company_profile.help_center_link if company_profile else "https://www.admin.algoview.in/login"  
contact_number = company_profile.company_phone_number if company_profile else None
company_name = company_profile.company_name if company_profile else "AlgoView"
company_sender_name=company_profile.company_sender_name if company_profile else "AlgoAdmin"
if company_profile and company_profile.company_logo:
    logo_url = settings.MEDIA_URL + str(company_profile.company_logo)  # Ensure full URL
else:
    logo_url = static('company_logos/download.png')  # Fallback to a default logo
smtp_details=smtp_details if smtp_details else None
# smtp_details=CompanySmtpDetails.objects.first()
default_from_email=smtp_details.email_host_user if smtp_details else   "no-reply@example.com"

def _get_default_from_email():
    smtp_details = get_smtp_details()
    return (
        getattr(smtp_details, "default_from_email", None)
        or getattr(smtp_details, "email_host_user", None)
        or settings.DEFAULT_FROM_EMAIL
    )

#client inactive and license expir ations
@shared_task
def send_client_acc_email_async(subject,messages,username,useremail):
        smtp_connection = get_smtp_connection()
        if not smtp_connection:
            print(f"SMTP connection could not be established!")
            return
        subject=subject
        from_email = _get_default_from_email()
        context = {
            'user_name': username,          
            'support_email': support_email, 
            'company_website':company_website , 
            "messages":messages,
            "company_name":company_name,
            "logo_url":logo_url
        }
        html_message = render_to_string('login_account_email.html', context)
        # print("html_message",html_message)

        email_message = EmailMultiAlternatives(subject, "", f"{company_sender_name} <{from_email}>", [useremail],connection=smtp_connection)
        email_message.attach_alternative(html_message, "text/html") 
        email_message.send()
#login opt email
@shared_task
def send_email_async(user_name, otp_code, email):
    smtp_connection = get_smtp_connection()
    if not smtp_connection:
        print(f"SMTP connection could not be established!")
        return
    subject=f"Your OTP for {company_name} Login"
    from_email = _get_default_from_email()
    # Define the context for the email template
    print("logo_url**************",logo_url)
    context = {
        'user_name': user_name,
        'otp_code': otp_code,            
        'valid_for_minutes': 2, 
        'support_email': support_email,  
        'company_website':company_website, 
        'logo_url':logo_url,
        'help_center': help_center_link,
        'contact_number': contact_number,
        'company_name':company_name
    }
    html_message = render_to_string('login_email.html', context)
    try:
        email_message = EmailMultiAlternatives(subject, "", f"{company_sender_name} <{from_email}>", [email], connection=smtp_connection)
        email_message.attach_alternative(html_message, "text/html")
        email_message.send()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Email sending failed: {e}")
    # send_mail(subject, message, from_email, recipient_list)
   
# tasks.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
@shared_task
def send_email_pass_async(email, password, user_name, login_link, support_email, help_center_link, company_website, contact_number):
        smtp_connection = get_smtp_connection()
        if not smtp_connection:
            print("SMTP connection could not be established!")
            return
        subject = f'Welcome to {company_name}! Your Registration is Complete'
        # subject = "Welcome to AlgoView Technologies"
        print("email sentdd")
        from_email = _get_default_from_email()
        # Render the HTML template with context data
        context = {
            'user_name': user_name,
            'password': password,
            'login_link': login_link,
            'support_email': support_email,
            'help_center': help_center_link,
            'company_website': company_website,
            'contact_number': contact_number,
            'company_name':company_name,
            'logo_url':logo_url
        }
        html_message = render_to_string('welcome_email.html', context)
        # print("html msg:::::::",html_message)
        from_email = _get_default_from_email()
        
        # Create the email
        email_message = EmailMultiAlternatives(subject, "", f"{company_sender_name} <{from_email}>", [email],connection=smtp_connection)
        email_message.attach_alternative(html_message, "text/html")  # Attach the HTML version

        # Send the email
        email_message.send()

@shared_task
def send_kyc_email_async(email, from_email, user_name, action, reason):
    smtp_connection = get_smtp_connection()
    if not smtp_connection:
        print("SMTP connection could not be established!")
        return
    if isinstance(email, list):
        email = email[0]  
    if isinstance(from_email, list):
        from_email = from_email[0]
    if action == 'approve':
        subject = "Your KYC has been approved"
    else:
        subject = "Your KYC has been rejected"

    context = {
        'user_name': user_name,
        'action': action,
        'reason': reason,
        'support_email': support_email,
        'help_center': help_center_link,
        'company_website': company_website,
        'contact_number': contact_number,
        "company_name":company_name,
        "logo_url":logo_url
    }
    html_message = render_to_string('kyc_email.html', context)
  
    # Create the email with an HTML alternative
    email_message = EmailMultiAlternatives(subject, "",f"{company_sender_name} <{from_email}>", [email],connection=smtp_connection)
    email_message.attach_alternative(html_message, "text/html")
    email_message.send()
    

@shared_task
def send_trade_email_async(email, from_email, user_name, status, reason):
    smtp_connection = get_smtp_connection()
    if not smtp_connection:
        print("SMTP connection could not be established!")
        logger.info(f"{user_name} : SMTP connection could not be established")
        return
    if isinstance(email, list):
        email = email[0]  
    if isinstance(from_email, list):
        from_email = from_email[0]
    subject="email for trade order!!!!!!!!!!!!"
    context = {
        'user_name': user_name,
        'status':status,
        'reason': reason,
        'support_email': support_email,
        'help_center': help_center_link,
        'company_website': company_website,
        'contact_number': contact_number,
        "company_name":company_name,
        "logo_url":logo_url
    }
    html_message = render_to_string('trade.html', context)
  
    # Create the email with an HTML alternative
    email_message = EmailMultiAlternatives(subject, "", f"{company_sender_name} <{from_email}>", [email],connection=smtp_connection)
    email_message.attach_alternative(html_message, "text/html")
    email_message.send()
    logger.info(f"{user_name} : Email has been sent !")
    
@shared_task
def resend_otp_email_async(user_email, otp_code):
    smtp_connection = get_smtp_connection()
    if not smtp_connection:
        print("SMTP connection could not be established!")
        return
    # Define the context for the email template
    context = {
        'otp_code': otp_code,
        'valid_for_minutes': 2,  # Adjust as needed
        'support_email': support_email,
        'company_website': company_website,
        'logo_url': logo_url,
        "company_name":company_name,
    }

    # Render the HTML message from the template
    html_message = render_to_string('resend_email.html', context)
    
    subject = 'Your OTP Code for Login'
    from_email = _get_default_from_email()
    
    try:
        email_message = EmailMultiAlternatives(subject, "", f"{company_sender_name} <{from_email}>", [user_email],connection=smtp_connection)
        email_message.attach_alternative(html_message, "text/html")
        email_message.send()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Email sending failed: {e}")
@shared_task
def send_login_success_email(username, email, browser, ip_address, login_time):
    smtp_connection = get_smtp_connection()
    if not smtp_connection:
        print("SMTP connection could not be established!")
        return
    subject = f"Login Alert for your {company_name} account!"
    from_email = _get_default_from_email()
    recipient_email = email  # FIXED: Use actual email, not username

    # Email context
    context = {
        'user_name': username,
        'user_email': email,
        'device': browser,
        'time': login_time,
        'ip_address': ip_address,
        'company_name': company_name,
        'company_url':company_website,
        'appstore_icon_url': "https://link-to-appstore-icon.png",
        'contact_number': contact_number,
        'address': "123 Business Street,indore M.P.",
        'logout_link': "https://sparksadmin.algoview.in/logout",
        "logo_url":logo_url
    }

    # Render HTML email
    html_message = render_to_string('login_success_email.html', context)
    print("from_email>>>>>>>",from_email)
    # Send Email
    try:
        email_message = EmailMultiAlternatives(subject, "", f"{company_sender_name} <{from_email}>", [recipient_email],connection=smtp_connection)
        email_message.attach_alternative(html_message, "text/html")
        email_message.send()
        print(f"Login success email sent to {recipient_email}")
    except Exception as e:
        print(f"Failed to send login success email: {e}")

@shared_task
def send_password_reset_email(uid, email, username, token):
    smtp_connection = get_smtp_connection()
    if not smtp_connection:
        print("SMTP connection could not be established!")
        return
    reset_link = f'{settings.FRONTEND_APP_URL}/pages/authentication/reset-password/:{uid}/:{token}/:layout'
    
    subject = "Password Reset Request"
    context = {
        'user_name': username,
        'reset_link': reset_link,
        'company_name': company_name, 
        'company_url': company_website,
        'support_email': support_email,
        'logo_url':logo_url
    }
    
    html_message = render_to_string('password_reset_email.html', context)
    from_email = _get_default_from_email()
    try:
        email_message = EmailMultiAlternatives(subject, "", f"{company_sender_name} <{from_email}>", [email],connection=smtp_connection)
      
        email_message.attach_alternative(html_message, "text/html")
        email_message.send()
        print(f"Password reset email sent to {email}")
    except Exception as e:
        logger.error("Password reset email failed", extra={"error": str(e)})
