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

#client inactive and license expir ations
@shared_task
def send_client_acc_email_async(subject,messages,username,useremail):
        subject=subject
        from_email = settings.DEFAULT_FROM_EMAIL
        context = {
            'user_name': username,          
            'support_email': 'support@company.com', 
            'company_website':settings.COMPANY_WEBSITE , 
            "messages":messages
        }
        html_message = render_to_string('login_account_email.html', context)
        # print("html_message",html_message)

        email_message = EmailMultiAlternatives(subject, "", from_email, [useremail])
        email_message.attach_alternative(html_message, "text/html") 
        email_message.send()
#login opt email
@shared_task
def send_email_async(user_name, otp_code, email):
        subject='Your Login OTP for AlgoView Technologies'
        from_email = settings.DEFAULT_FROM_EMAIL
        # Define the context for the email template
        context = {
            'user_name': user_name,
            'otp_code': otp_code,            
            'valid_for_minutes': 2, 
            'support_email': 'support@company.com',  
            'company_website':settings.COMPANY_WEBSITE , 
        }

        html_message = render_to_string('login_email.html', context)
      
        email_message = EmailMultiAlternatives(subject, "", from_email, [email])
        email_message.attach_alternative(html_message, "text/html")  # Attach the HTML version
        email_message.send()
    # send_mail(subject, message, from_email, recipient_list)

# tasks.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
@shared_task
def send_email_pass_async(email, password, user_name, login_link, support_email, help_center_link, company_website, contact_number):
        subject = 'Welcome to AlgoView Technologies! Your Registration is Complete'
        # subject = "Welcome to AlgoView Technologies"
        print("email sentdd")
        from_email = settings.DEFAULT_FROM_EMAIL
        # Render the HTML template with context data
        context = {
            'user_name': user_name,
            'password': password,
            'login_link': login_link,
            'support_email': support_email,
            'help_center': help_center_link,
            'company_website': company_website,
            'contact_number': contact_number
        }
        html_message = render_to_string('welcome_email.html', context)
        # print("html msg:::::::",html_message)
        from_email = settings.DEFAULT_FROM_EMAIL
        
        # Create the email
        email_message = EmailMultiAlternatives(subject, "", from_email, [email])
        email_message.attach_alternative(html_message, "text/html")  # Attach the HTML version

        # Send the email
        email_message.send()
        
support_email=settings.DEFAULT_FROM_EMAIL
contact_number=settings.CONTACT_NUM
login_link=settings.LOGIN_LINK
help_center_link=settings.HELP_CENTER_LINK
company_website=settings.COMPANY_WEBSITE 
@shared_task
def send_kyc_email_async(email, from_email, user_name, action, reason):
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
        'contact_number': contact_number
    }
    html_message = render_to_string('kyc_email.html', context)
  
    # Create the email with an HTML alternative
    email_message = EmailMultiAlternatives(subject, "", from_email, [email])
    email_message.attach_alternative(html_message, "text/html")
    email_message.send()
    

@shared_task
def send_trade_email_async(email, from_email, user_name, status, reason):
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
        'contact_number': contact_number
    }
    html_message = render_to_string('trade.html', context)
  
    # Create the email with an HTML alternative
    email_message = EmailMultiAlternatives(subject, "", from_email, [email])
    email_message.attach_alternative(html_message, "text/html")
    email_message.send()
    
