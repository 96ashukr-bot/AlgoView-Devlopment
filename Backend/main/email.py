from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags
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
            from_email = settings.DEFAULT_FROM_EMAIL
            send_mail(subject, message, from_email, [email])
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

class EmailService:
    
    @staticmethod
    def send_password_email(email, password, user_name, login_link, support_email, help_center_link, company_website, contact_number):
        subject = 'Welcome to AlgoView Technologies! Your Registration is Complete'
        # subject = "Welcome to AlgoView Technologies"
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
        
    @staticmethod
    def send_login_email_otp(email, otp_code, user_name):
        subject='Your Login OTP for AlgoView Technologies'
        from_email = settings.DEFAULT_FROM_EMAIL
        # Define the context for the email template
        context = {
            'user_name': user_name,           # User's name
            'otp_code': otp_code,             # One-Time Password
            'valid_for_minutes': 2,  # OTP expiration time
            'support_email': 'support@company.com',  # Support email
            'company_website':settings.COMPANY_WEBSITE ,  # Company website link
        }

        # Render the HTML email template
        html_message = render_to_string('login_email.html', context)
        # plain_message = strip_tags(html_message)  # For non-HTML email clients
# Create the email
        email_message = EmailMultiAlternatives(subject, "", from_email, [email])
        email_message.attach_alternative(html_message, "text/html")  # Attach the HTML version

        # Send the email
        email_message.send()
  

