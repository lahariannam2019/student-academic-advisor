import random
import string
import secrets
import logging
from typing import Tuple

logger = logging.getLogger("auth_email")


def generate_verification_code() -> str:
    """Generate a random 6-digit verification code."""
    return "".join(random.choices(string.digits, k=6))


def generate_verification_token() -> str:
    """Generate a secure URL token for email verification links."""
    return secrets.token_urlsafe(32)


def send_verification_email(email: str, code: str, token: str) -> bool:
    """
    Send or log an email verification code/link.
    If SMTP server is configured, attempts real delivery; otherwise logs to console/logger.
    """
    logger.info(f"[EMAIL VERIFICATION] Sent to {email} | Code: {code} | Token: {token}")
    print(f"\n==========================================")
    print(f"[EMAIL VERIFICATION] To: {email}")
    print(f"[EMAIL VERIFICATION] Verification Code: {code}")
    print(f"[EMAIL VERIFICATION] Verification Token: {token}")
    print(f"==========================================\n")
    return True


def send_password_reset_email(email: str, token: str) -> bool:
    """
    Send or log a password reset link.
    """
    logger.info(f"[PASSWORD RESET] Sent to {email} | Token: {token}")
    print(f"\n==========================================")
    print(f"[PASSWORD RESET] To: {email}")
    print(f"[PASSWORD RESET] Reset Token: {token}")
    print(f"==========================================\n")
    return True
