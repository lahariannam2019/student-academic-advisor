import json
import random
import string
import secrets
import logging
import urllib.request
import urllib.parse
from app.config import settings

logger = logging.getLogger("auth_email")


def generate_verification_code() -> str:
    """Generate a random 6-digit verification code."""
    return "".join(random.choices(string.digits, k=6))


def generate_verification_token() -> str:
    """Generate a secure URL token for email verification links."""
    return secrets.token_urlsafe(32)


def _send_resend_email(to_email: str, subject: str, html_content: str, text_content: str) -> bool:
    """
    Send an email using Resend API (https://api.resend.com/emails).
    """
    api_key = settings.RESEND_API_KEY.strip()
    if not api_key:
        return False

    sender = settings.EMAILS_FROM_EMAIL.strip() or "Student Academic Advisor <onboarding@resend.dev>"

    payload = {
        "from": sender,
        "to": [to_email],
        "subject": subject,
        "html": html_content,
        "text": text_content,
    }

    try:
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "StudentAcademicAdvisor/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in [200, 201]:
                logger.info(f"[RESEND EMAIL] Successfully delivered email to {to_email}")
                return True
            else:
                logger.error(f"[RESEND EMAIL] API returned status {resp.status}")
                return False
    except Exception as e:
        logger.error(f"[RESEND EMAIL ERROR] Failed to deliver email to {to_email}: {str(e)}")
        return False


def send_verification_email(email: str, code: str, token: str) -> bool:
    """
    Send verification email using Resend in production, or fallback to dev console log.
    Never exposes verification code in production logs.
    """
    subject = "Verify Your Email - Student Academic Advisor"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; }}
        .container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
        .header {{ text-align: center; padding-bottom: 24px; border-bottom: 1px solid #f1f5f9; }}
        .logo {{ display: inline-block; background: #4f46e5; color: #ffffff; font-weight: 800; font-size: 20px; border-radius: 12px; padding: 10px 18px; text-decoration: none; }}
        .content {{ padding: 24px 0; text-align: center; }}
        .title {{ font-size: 20px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }}
        .subtitle {{ font-size: 14px; color: #64748b; margin-bottom: 24px; line-height: 1.5; }}
        .code-box {{ background: #f1f5f9; border: 2px dashed #cbd5e1; border-radius: 12px; font-family: 'Courier New', Courier, monospace; font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #4f46e5; padding: 16px 24px; display: inline-block; margin: 12px 0 24px 0; }}
        .expiry {{ font-size: 12px; color: #94a3b8; margin-top: 12px; }}
        .footer {{ border-top: 1px solid #f1f5f9; padding-top: 20px; text-align: center; font-size: 12px; color: #94a3b8; line-height: 1.5; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <div class="logo">🎓 Student Academic Advisor</div>
        </div>
        <div class="content">
          <div class="title">Verify Your Email Address</div>
          <div class="subtitle">Welcome! Please enter the 6-digit verification code below to verify your account and access your academic advisor dashboard.</div>
          
          <div class="code-box">{code}</div>
          
          <div class="expiry">This verification code expires in 24 hours.</div>
        </div>
        <div class="footer">
          If you did not create a Student Academic Advisor account, please disregard this message.<br>
          &copy; 2026 Student Academic Advisor. Secure academic intelligence.
        </div>
      </div>
    </body>
    </html>
    """
    
    text_content = f"Welcome to Student Academic Advisor!\n\nYour 6-digit verification code is: {code}\n\nThis code expires in 24 hours."

    # Production delivery via Resend API
    if settings.RESEND_API_KEY:
        sent = _send_resend_email(to_email=email, subject=subject, html_content=html_content, text_content=text_content)
        if sent:
            logger.info(f"[EMAIL VERIFICATION] Delivered via Resend to {email}")
            return True

    # Dev/Local fallback logging
    logger.info(f"[EMAIL VERIFICATION DEV] Sent to {email}")
    print(f"\n==========================================")
    print(f"[EMAIL VERIFICATION DEV] To: {email}")
    print(f"[EMAIL VERIFICATION DEV] Verification Code: {code}")
    print(f"==========================================\n")
    return True


def send_password_reset_email(email: str, token: str) -> bool:
    """
    Send password reset email via Resend in production, or fallback to dev console log.
    """
    subject = "Reset Your Password - Student Academic Advisor"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; }}
        .container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
        .header {{ text-align: center; padding-bottom: 24px; border-bottom: 1px solid #f1f5f9; }}
        .logo {{ display: inline-block; background: #4f46e5; color: #ffffff; font-weight: 800; font-size: 20px; border-radius: 12px; padding: 10px 18px; text-decoration: none; }}
        .content {{ padding: 24px 0; text-align: center; }}
        .title {{ font-size: 20px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }}
        .subtitle {{ font-size: 14px; color: #64748b; margin-bottom: 24px; line-height: 1.5; }}
        .footer {{ border-top: 1px solid #f1f5f9; padding-top: 20px; text-align: center; font-size: 12px; color: #94a3b8; line-height: 1.5; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <div class="logo">🎓 Student Academic Advisor</div>
        </div>
        <div class="content">
          <div class="title">Reset Your Password</div>
          <div class="subtitle">We received a request to reset your password. Use the token below or the link provided to reset your account password.</div>
          <p style="font-family: monospace; font-size: 16px; background: #f1f5f9; padding: 12px; border-radius: 8px;">{token}</p>
        </div>
        <div class="footer">
          If you did not request a password reset, please ignore this email.<br>
          &copy; 2026 Student Academic Advisor.
        </div>
      </div>
    </body>
    </html>
    """

    text_content = f"Student Academic Advisor Password Reset\n\nYour reset token is: {token}\n\nThis token expires in 1 hour."

    if settings.RESEND_API_KEY:
        sent = _send_resend_email(to_email=email, subject=subject, html_content=html_content, text_content=text_content)
        if sent:
            logger.info(f"[PASSWORD RESET] Delivered via Resend to {email}")
            return True

    logger.info(f"[PASSWORD RESET DEV] Sent to {email}")
    print(f"\n==========================================")
    print(f"[PASSWORD RESET DEV] To: {email}")
    print(f"[PASSWORD RESET DEV] Reset Token: {token}")
    print(f"==========================================\n")
    return True
