import logging
import re
from typing import Any

# Configure root logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger("nena-ai")

SENSITIVE_PATTERNS = [
    (re.compile(r'otp[:=]\s*["\']?(\d{6})["\']?', re.IGNORECASE), "otp=******"),
    (re.compile(r'Bearer\s+[A-Za-z0-9\-_.]+', re.IGNORECASE), "Bearer [REDACTED]"),
    (re.compile(r'apiKey[:=]\s*["\']?[A-Za-z0-9\-_.]+["\']?', re.IGNORECASE), "apiKey=[REDACTED]"),
    (re.compile(r'fingerprint[:=]\s*["\']?([A-Za-z0-9\-_.]+)["\']?', re.IGNORECASE), "fingerprint=[REDACTED]"),
]


def mask_sensitive_data(message: str) -> str:
    """Masks OTPs, tokens, and sensitive credentials in log output."""
    for pattern, replacement in SENSITIVE_PATTERNS:
        message = pattern.sub(replacement, message)
    return message


class SafeLogger:
    def __init__(self, name: str):
        self._log = logging.getLogger(name)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.info(mask_sensitive_data(str(msg)), *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.warning(mask_sensitive_data(str(msg)), *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.error(mask_sensitive_data(str(msg)), *args, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.debug(mask_sensitive_data(str(msg)), *args, **kwargs)


safe_logger = SafeLogger("nena.safe")
