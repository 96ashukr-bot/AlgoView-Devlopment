from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError


def verify_aws_instance_identity(pkcs7_value: str) -> dict:
    raw_pkcs7 = str(pkcs7_value or "").strip()
    if not raw_pkcs7 or len(raw_pkcs7) > 32768:
        raise ValidationError("Missing or invalid AWS instance identity signature.")
    if "-----BEGIN PKCS7-----" not in raw_pkcs7:
        raw_pkcs7 = f"-----BEGIN PKCS7-----\n{raw_pkcs7}\n-----END PKCS7-----\n"

    certificate_dir = Path(settings.AWS_IID_CERTIFICATE_DIR)
    candidate_certificates = sorted(certificate_dir.glob("*-dsa.pem"))
    if not candidate_certificates:
        raise ValidationError("AWS instance identity certificates are not installed.")

    verified_document = None
    with tempfile.TemporaryDirectory(prefix="algoview-aws-iid-") as temp_dir:
        signature_path = Path(temp_dir) / "identity.pkcs7"
        output_path = Path(temp_dir) / "document.json"
        signature_path.write_text(raw_pkcs7)
        for certificate_path in candidate_certificates:
            result = subprocess.run(
                [
                    "openssl", "smime", "-verify", "-in", str(signature_path),
                    "-inform", "PEM", "-certfile", str(certificate_path),
                    "-noverify", "-out", str(output_path),
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                try:
                    verified_document = json.loads(output_path.read_text())
                except (OSError, json.JSONDecodeError) as exc:
                    raise ValidationError("AWS returned a malformed instance identity document.") from exc
                break
    if not isinstance(verified_document, dict):
        raise ValidationError("AWS instance identity signature verification failed.")

    required = ("instanceId", "imageId", "region", "accountId", "architecture")
    missing = [field for field in required if not str(verified_document.get(field) or "").strip()]
    if missing:
        raise ValidationError(f"AWS instance identity is missing: {', '.join(missing)}.")
    if verified_document["region"] not in settings.AWS_AMI_ALLOWED_REGIONS:
        raise ValidationError("AWS instance region is not approved for AlgoView nodes.")
    if verified_document["architecture"] not in settings.AWS_AMI_ALLOWED_ARCHITECTURES:
        raise ValidationError("AWS instance architecture is not approved for AlgoView nodes.")
    if not settings.AWS_AMI_ALLOWED_IDS or verified_document["imageId"] not in settings.AWS_AMI_ALLOWED_IDS:
        raise ValidationError("This instance was not launched from an approved AlgoView AMI.")
    return verified_document
