from main.models import *

# company_profile=None
# smtp_details=None
company_profile = CompanyProfileDetails.objects.first()
smtp_details=CompanySmtpDetails.objects.first()