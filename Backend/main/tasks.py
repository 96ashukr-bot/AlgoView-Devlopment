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

@shared_task
def send_email_async(subject, message, from_email, recipient_list):
    send_mail(subject, message, from_email, recipient_list)
# tasks.py
@shared_task
def send_email_pass_async(email, password, user_name, login_link, support_email, help_center_link, company_website, contact_number):
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
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [email])
