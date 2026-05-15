from copy import deepcopy


BROKER_SETUP_SPECS = {
    "angel one": {
        "display_name": "Angel One",
        "slug": "angel-one",
        "auth_mode": "direct_credentials",
        "description": "Store Angel One credentials securely, then use the daily broker login flow to create a trading session.",
        "save_action_label": "Save Angel One API Details",
        "connect_action_label": "Generate Angel One Token",
        "connect_path": "/broker_auth_login/?broker=angel%20one",
        "supports_callback": True,
        "supports_redirect": True,
        "fields": [
            {"key": "broker_API_KEY", "label": "API Key", "type": "password", "required": True, "secret": True},
            {"key": "broker_Demate_User_Name", "label": "Client ID / User ID", "type": "text", "required": True, "secret": False},
            {"key": "broker_pass", "label": "Password", "type": "password", "required": True, "secret": True},
            {"key": "broker_Totp_Authcode", "label": "TOTP Secret", "type": "password", "required": True, "secret": True},
        ],
    },
    "upstox": {
        "display_name": "Upstox",
        "slug": "upstox",
        "auth_mode": "redirect_oauth",
        "description": "Save the Upstox API credentials, then use the broker redirect flow to connect the account.",
        "save_action_label": "Save Upstox API Details",
        "connect_action_label": "Connect to Upstox",
        "connect_path": "/broker_auth_login/?broker=upstox",
        "supports_callback": True,
        "supports_redirect": True,
        "fields": [
            {"key": "broker_API_KEY", "label": "API Key", "type": "password", "required": True, "secret": True},
            {"key": "broker_API_SKEY", "label": "API Secret Key", "type": "password", "required": True, "secret": True},
        ],
    },
    "zerodha": {
        "display_name": "Zerodha",
        "slug": "zerodha",
        "auth_mode": "redirect_oauth",
        "description": "Save Zerodha API credentials, then complete the broker-side login flow from the trading panel.",
        "save_action_label": "Save Zerodha API Details",
        "connect_action_label": "Connect to Zerodha",
        "connect_path": "/broker_auth_login/?broker=zerodha",
        "supports_callback": False,
        "supports_redirect": True,
        "fields": [
            {"key": "broker_API_KEY", "label": "API Key", "type": "password", "required": True, "secret": True},
            {"key": "broker_API_SKEY", "label": "API Secret Key", "type": "password", "required": True, "secret": True},
        ],
    },
    "alice blue": {
        "display_name": "Alice Blue",
        "slug": "alice-blue",
        "auth_mode": "direct_credentials",
        "description": "Save Alice Blue User ID and either ANT API Key, or Developer Portal API Secret plus fresh Vendor Auth Code, then generate the daily session through the assigned execution proxy/static IP.",
        "save_action_label": "Save Alice Blue API Details",
        "connect_action_label": "Generate Alice Blue Token",
        "connect_path": None,
        "supports_callback": True,
        "supports_redirect": False,
        "fields": [
            {"key": "broker_API_UID", "label": "User ID", "type": "text", "required": True, "secret": False},
            {"key": "broker_API_KEY", "label": "ANT API Key / App Code", "type": "password", "required": False, "secret": True},
            {"key": "broker_API_SKEY", "label": "Developer Portal API Secret", "type": "password", "required": False, "secret": True},
            {"key": "broker_Totp_Authcode", "label": "Vendor Auth Code", "type": "password", "required": False, "secret": True},
        ],
        "requirement_note": "ANT/pya3 login uses User ID + ANT API Key. Alice Blue Developer Portal apps use SHA-256(User ID + fresh authCode + API Secret), so save the Vendor Auth Code as well. API Key + Secret alone cannot create the daily vendor session.",
    },
    "5paisa": {
        "display_name": "5Paisa",
        "slug": "5paisa",
        "auth_mode": "redirect_oauth",
        "description": "Save the 5Paisa API credentials used for daily login/session generation.",
        "save_action_label": "Save 5Paisa API Details",
        "connect_action_label": "Connect to 5Paisa",
        "connect_path": "/broker_auth_login/?broker=5paisa",
        "supports_callback": True,
        "supports_redirect": True,
        "fields": [
            {"key": "broker_API_KEY", "label": "User Key", "type": "password", "required": True, "secret": True},
            {"key": "broker_API_SKEY", "label": "Encryption Key", "type": "password", "required": True, "secret": True},
            {"key": "broker_API_UID", "label": "Vendor User ID / User ID", "type": "text", "required": True, "secret": False},
        ],
        "requirement_note": "Use the 5Paisa vendor/API User ID that belongs to the User Key and Encryption Key. If 5Paisa returns 'Invalid Vendor UserID', this field does not match the app credentials.",
    },
    "fyers": {
        "display_name": "FYERS",
        "slug": "fyers",
        "auth_mode": "redirect_oauth",
        "description": "Save FYERS API credentials, then complete the broker login flow from the trading panel.",
        "save_action_label": "Save FYERS API Details",
        "connect_action_label": "Connect to FYERS",
        "connect_path": "/broker_auth_login/?broker=fyers",
        "supports_callback": False,
        "supports_redirect": True,
        "fields": [
            {"key": "broker_API_KEY", "label": "Client ID", "type": "password", "required": True, "secret": True},
            {"key": "broker_API_SKEY", "label": "Secret Key", "type": "password", "required": True, "secret": True},
        ],
    },
    "dhan": {
        "display_name": "Dhan",
        "slug": "dhan",
        "auth_mode": "redirect_oauth",
        "description": "Use either a Dhan Web access token, or save App/API Key + Secret + Client ID and complete Dhan's consent flow to generate an access token.",
        "save_action_label": "Save Dhan API Details",
        "connect_action_label": "Connect to Dhan",
        "connect_path": "/broker_auth_login/?broker=dhan",
        "supports_callback": True,
        "supports_redirect": True,
        "fields": [
            {"key": "broker_API_KEY", "label": "App ID / API Key", "type": "password", "required": False, "secret": True},
            {"key": "broker_API_SKEY", "label": "App Secret / API Secret", "type": "password", "required": False, "secret": True},
            {"key": "broker_API_UID", "label": "Dhan Client ID", "type": "text", "required": False, "secret": False},
            {"key": "access_token", "label": "Access Token", "type": "password", "required": False, "secret": True},
        ],
        "requirement_note": "Provide either Access Token, or App/API Key + Secret + Dhan Client ID for consent login.",
    },
}


BROKER_NAME_ALIASES = {
    "angle one": "angel one",
    "angelone": "angel one",
    "angleone": "angel one",
    "up stock": "upstox",
    "aliceblue": "alice blue",
    "alice-blue": "alice blue",
    "5 paisa": "5paisa",
    "five paisa": "5paisa",
}


def normalize_broker_name(name):
    if not name:
        return ""
    normalized = str(name).strip().lower()
    normalized = " ".join(normalized.replace("_", " ").replace("-", " ").split())
    return BROKER_NAME_ALIASES.get(normalized, normalized)


def get_broker_setup_spec(broker_name):
    return deepcopy(BROKER_SETUP_SPECS.get(normalize_broker_name(broker_name)))


def resolve_broker_value(instance, key):
    if not instance:
        return None
    if key == "broker_API_SKEY":
        return instance.get_broker_api_secret() if instance.is_angel_one_broker() else instance.broker_API_SKEY
    if key == "broker_pass":
        return instance.get_broker_password()
    if key == "broker_Totp_Authcode":
        return instance.get_broker_totp_secret()
    if key == "access_token":
        return instance.get_access_token_secure() if instance.is_angel_one_broker() else instance.access_token
    return getattr(instance, key, None)


def broker_field_is_configured(instance, key):
    value = resolve_broker_value(instance, key)
    if isinstance(value, str):
        value = value.strip()
    return bool(value)


def mask_field_value(value):
    if value is None:
        return None
    value = str(value)
    if len(value) <= 4:
        return "*" * len(value)
    return f"{'*' * max(len(value) - 4, 4)}{value[-4:]}"


def build_field_state(instance, field_spec):
    value = resolve_broker_value(instance, field_spec["key"])
    configured = broker_field_is_configured(instance, field_spec["key"])
    state = {
        "key": field_spec["key"],
        "label": field_spec["label"],
        "type": field_spec["type"],
        "required": field_spec.get("required", False),
        "secret": field_spec.get("secret", False),
        "configured": configured,
        "persisted": configured,
        "value": None,
        "display_value": None,
    }
    if not configured:
        return state
    if field_spec.get("secret", False):
        state["display_value"] = "Saved"
    else:
        state["value"] = value
        state["display_value"] = value
    if field_spec["key"] == "broker_API_KEY":
        state["masked_value"] = mask_field_value(value)
    return state


def build_broker_setup_schema(broker_name, instance=None):
    spec = get_broker_setup_spec(broker_name)
    if not spec:
        return None
    spec["fields"] = [build_field_state(instance, field_spec) for field_spec in spec["fields"]]
    return spec


def list_broker_schemas(brokers, client_broker_detail=None):
    items = []
    selected_name = normalize_broker_name(
        client_broker_detail.broker_name.broker_name if client_broker_detail and client_broker_detail.broker_name else None
    )
    for broker in brokers:
        spec = build_broker_setup_schema(broker.broker_name, client_broker_detail if normalize_broker_name(broker.broker_name) == selected_name else None)
        items.append({
            "id": broker.id,
            "broker_name": spec["display_name"] if spec else broker.broker_name,
            "is_active": broker.is_active,
            "description": broker.description,
            "setup_schema": spec,
        })
    return items


def get_default_broker_catalog():
    catalog = []
    for normalized_name, spec in BROKER_SETUP_SPECS.items():
        catalog.append({
            "broker_name": spec["display_name"],
            "description": spec.get("description"),
            "is_active": True,
            "normalized_name": normalized_name,
        })
    return catalog
