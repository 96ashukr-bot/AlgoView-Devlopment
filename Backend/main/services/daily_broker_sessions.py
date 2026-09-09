"""Daily client trading-session policy. All boundaries are explicitly in IST."""
from datetime import datetime, time
from zoneinfo import ZoneInfo

from django.utils import timezone

IST = ZoneInfo("Asia/Kolkata")


def aware(value):
    return timezone.make_aware(value, IST) if timezone.is_naive(value) else value


def daily_cutoff(issued_at):
    return datetime.combine(aware(issued_at).astimezone(IST).date(), time(23, 55), IST)


def capped_expiry(issued_at, broker_expiry=None):
    cutoff = daily_cutoff(issued_at)
    return min(cutoff, aware(broker_expiry)) if broker_expiry else cutoff


def session_policy_error(details, *, now=None, refresh=False, require_token=True):
    if details is None:
        return "Broker session is missing. Generate today's broker token."
    if refresh:
        details.refresh_from_db(fields=["tokenCreatedAt", "access_token_expiry", "isTokenExpired", "access_token", "encrypted_access_token"])
    if require_token:
        secure_getter = getattr(details, "get_access_token_secure", None)
        token = secure_getter() if callable(secure_getter) else None
        if not str(token or getattr(details, "access_token", None) or "").strip():
            return "Broker token is missing. Generate today's broker token before trading."
    now = aware(now or timezone.now())
    issued = getattr(details, "tokenCreatedAt", None)
    if not issued or aware(issued) > now or aware(issued).astimezone(IST).date() != now.astimezone(IST).date():
        return "Today's broker token is required. Generate a fresh broker token before trading."
    if now >= daily_cutoff(issued):
        return "Broker token expired at 11:55 PM IST. Generate a fresh token on the next day."
    expiry = getattr(details, "access_token_expiry", None)
    if getattr(details, "isTokenExpired", False) or (expiry and now >= aware(expiry)):
        return "Broker token has expired. Generate a fresh broker token before trading."
    return None


def expire_due_client_tokens(now=None):
    """Conditional bulk update cannot invalidate a concurrently renewed session."""
    from django.db.models import Q
    from main.models import ClientBrokerdetails
    now = aware(now or timezone.now())
    local = now.astimezone(IST)
    day_start = datetime.combine(local.date(), time.min, IST)
    due = Q(tokenCreatedAt__lt=day_start) | Q(tokenCreatedAt__isnull=True) | Q(access_token_expiry__lte=now)
    if now >= daily_cutoff(now):
        due |= Q(tokenCreatedAt__lt=now)
    return ClientBrokerdetails.objects.exclude(broker_name__broker_name__iexact="Demo Broker").filter(due).exclude(isTokenExpired=True).update(isTokenExpired=True)
