import logging

from main.angelone.utils.redaction import redact_secrets, sanitize_text


class SecretRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = sanitize_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = redact_secrets(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(redact_secrets(sanitize_text(value)) for value in record.args)
            else:
                record.args = redact_secrets(sanitize_text(record.args))
        return True
