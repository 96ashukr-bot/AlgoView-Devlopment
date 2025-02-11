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

from main.models import *
from main.utils import get_smtp_connection
from django.templatetags.static import static
    # Get company profile for support email and website
company_profile = CompanyProfileDetails.objects.first()
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

smtp_details=CompanySmtpDetails.objects.first()
default_from_email=smtp_details.default_from_email if smtp_details else   "no-reply@example.com"
print("default_from_email>>>>>>",default_from_email)
#client inactive and license expir ations
@shared_task
def send_client_acc_email_async(subject,messages,username,useremail):
        smtp_connection = get_smtp_connection()
        if not smtp_connection:
            print(f"SMTP connection could not be established!")
            return
        subject=subject
        from_email =default_from_email
        context = {
            'user_name': username,          
            'support_email': support_email, 
            'company_website':company_website , 
            "messages":messages,
            "company_name":company_name,
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
    from_email = default_from_email
    # Define the context for the email template
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
        from_email = default_from_email
        # Render the HTML template with context data
        context = {
            'user_name': user_name,
            'password': password,
            'login_link': login_link,
            'support_email': support_email,
            'help_center': help_center_link,
            'company_website': company_website,
            'contact_number': contact_number,
            'company_name':company_name
        }
        html_message = render_to_string('welcome_email.html', context)
        # print("html msg:::::::",html_message)
        from_email = default_from_email
        
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
    }
    html_message = render_to_string('trade.html', context)
  
    # Create the email with an HTML alternative
    email_message = EmailMultiAlternatives(subject, "", f"{company_sender_name} <{from_email}>", [email],connection=smtp_connection)
    email_message.attach_alternative(html_message, "text/html")
    email_message.send()
    
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
        'logo': logo_url,
        "company_name":company_name,
    }

    # Render the HTML message from the template
    html_message = render_to_string('resend_email.html', context)
    
    subject = 'Your OTP Code for Login'
    from_email = default_from_email  # Or whatever the default is for your project
    
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
    from_email = default_from_email  # Ensure it's defined in settings.py
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
