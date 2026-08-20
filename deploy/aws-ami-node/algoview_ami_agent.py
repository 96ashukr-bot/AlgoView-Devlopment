#!/usr/bin/env python3
"""AlgoView AWS AMI bootstrap agent. Uses only the Python standard library."""

import json
import os
import platform
import secrets
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path


ENV_PATH = Path("/etc/algoview-node/agent.env")
STATE_DIR = Path("/var/lib/algoview-node")
CREDENTIALS_PATH = STATE_DIR / "proxy-credentials.json"
TINYPROXY_CONFIG = Path("/etc/tinyproxy/tinyproxy.conf")
IMDS_BASE = "http://169.254.169.254/latest"


def load_env(path=ENV_PATH):
    values = {}
    if path.exists():
        for raw_line in path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    values.update({key: value for key, value in os.environ.items() if key.startswith("ALGOVIEW_")})
    return values


def imds_token():
    request = urllib.request.Request(f"{IMDS_BASE}/api/token", method="PUT", headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"})
    with urllib.request.urlopen(request, timeout=3) as response:
        return response.read().decode().strip()


def imds_get(path, token):
    request = urllib.request.Request(f"{IMDS_BASE}/{path.lstrip('/')}", headers={"X-aws-ec2-metadata-token": token})
    with urllib.request.urlopen(request, timeout=3) as response:
        return response.read().decode().strip()


def instance_identity_pkcs7():
    token = imds_token()
    return imds_get("dynamic/instance-identity/pkcs7", token)


def load_or_create_credentials():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if CREDENTIALS_PATH.exists():
        return json.loads(CREDENTIALS_PATH.read_text())
    credentials = {
        "proxy_username": f"av_{secrets.token_hex(12)}",
        "proxy_password": secrets.token_urlsafe(48),
    }
    CREDENTIALS_PATH.write_text(json.dumps(credentials))
    CREDENTIALS_PATH.chmod(0o600)
    return credentials


def configure_tinyproxy(credentials, *, port, allowed_ip):
    allow_line = f"Allow {allowed_ip}\n" if allowed_ip else ""
    config = f"""User tinyproxy
Group tinyproxy
Port {int(port)}
Listen 0.0.0.0
Timeout 60
DefaultErrorFile \"/usr/share/tinyproxy/default.html\"
StatFile \"/usr/share/tinyproxy/stats.html\"
LogFile \"/var/log/tinyproxy/tinyproxy.log\"
LogLevel Info
PidFile \"/run/tinyproxy/tinyproxy.pid\"
MaxClients 100
StartServers 2
MinSpareServers 2
MaxSpareServers 5
BasicAuth {credentials['proxy_username']} {credentials['proxy_password']}
{allow_line}ConnectPort 443
DisableViaHeader Yes
"""
    if not TINYPROXY_CONFIG.exists() or TINYPROXY_CONFIG.read_text() != config:
        TINYPROXY_CONFIG.write_text(config)
        TINYPROXY_CONFIG.chmod(0o600)
        subprocess.run(["systemctl", "restart", "tinyproxy"], check=True)


def register(config, credentials):
    payload = {
        **credentials,
        "agent_version": config.get("ALGOVIEW_AMI_AGENT_VERSION", "1"),
        "instance_identity_pkcs7": instance_identity_pkcs7(),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    url = config["ALGOVIEW_MAIN_SERVER_URL"].rstrip("/") + "/api/node/aws-ami/register/"
    request = urllib.request.Request(url, data=encoded, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.status, json.loads(response.read().decode())


def main():
    config = load_env()
    if not config.get("ALGOVIEW_MAIN_SERVER_URL"):
        raise SystemExit("ALGOVIEW_MAIN_SERVER_URL is required.")
    proxy_port = int(config.get("ALGOVIEW_AMI_PROXY_PORT", "3128"))
    credentials = load_or_create_credentials()
    configure_tinyproxy(credentials, port=proxy_port, allowed_ip=config.get("ALGOVIEW_MAIN_SERVER_IP", ""))

    while True:
        try:
            status_code, result = register(config, credentials)
            print(json.dumps({"http_status": status_code, "registration": result}, sort_keys=True), flush=True)
            time.sleep(300 if result.get("status") == "activated" else 10)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")[:1000]
            print(f"Registration waiting: HTTP {exc.code}: {body}", flush=True)
            time.sleep(10 if exc.code in {400, 404, 409, 429} else 30)
        except Exception as exc:
            print(f"AMI agent error: {exc}", flush=True)
            time.sleep(30)


if __name__ == "__main__":
    main()
