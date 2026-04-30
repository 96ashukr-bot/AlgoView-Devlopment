from main.models import CompanyProfileDetails, CompanySmtpDetails

def get_company_profile():
    try:
        return CompanyProfileDetails.objects.first()
    except Exception:
        return None


def get_smtp_details():
    try:
        return CompanySmtpDetails.objects.order_by("-id").first()
    except Exception:
        return None
   
