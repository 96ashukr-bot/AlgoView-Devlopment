# from main.models import *

# # company_profile=None
# # smtp_details=None
# company_profile = CompanyProfileDetails.objects.first() or None

# smtp_details=CompanySmtpDetails.objects.first() or None


from main.models import CompanyProfileDetails, CompanySmtpDetails

# Do NOT run DB queries at the top level

def get_company_profile():
    from django.db import connection
    if connection.connection and connection.connection.closed:
        return None
    try:
        return CompanyProfileDetails.objects.first()
    except Exception:
        return None

def get_smtp_details():
    from django.db import connection
    if connection.connection and connection.connection.closed:
        return None
    try:
        return CompanySmtpDetails.objects.first()
    except Exception:
        return None
