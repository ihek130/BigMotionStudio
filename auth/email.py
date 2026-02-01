"""
Email Utility - Send transactional emails (password reset, verification, etc.)
Uses Resend for professional email delivery.
"""

import os
import logging
from typing import Optional
import resend

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "support@bigmotionstudio.com")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Initialize Resend
resend.api_key = RESEND_API_KEY


# =============================================================================
# Email Templates
# =============================================================================

def get_reset_password_email(reset_token: str, user_email: str) -> tuple[str, str]:
    """
    Generate password reset email content.
    Returns: (subject, html_body)
    """
    reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"
    
    subject = "Reset Your Password - Big Motion Studio"
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f0fdf4;">
    <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
        <!-- Header -->
        <div style="text-align: center; margin-bottom: 32px;">
            <div style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #14b8a6 100%); padding: 16px; border-radius: 16px; margin-bottom: 16px;">
                <span style="font-size: 32px;">🎬</span>
            </div>
            <h1 style="color: #059669; margin: 0; font-size: 24px; font-weight: bold;">Big Motion Studio</h1>
        </div>
        
        <!-- Card -->
        <div style="background: white; border-radius: 16px; padding: 40px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            <h2 style="color: #1f2937; margin: 0 0 16px 0; font-size: 20px; text-align: center;">Reset Your Password</h2>
            
            <p style="color: #6b7280; font-size: 16px; line-height: 1.6; margin: 0 0 24px 0; text-align: center;">
                We received a request to reset the password for your account associated with <strong>{user_email}</strong>.
            </p>
            
            <p style="color: #6b7280; font-size: 16px; line-height: 1.6; margin: 0 0 32px 0; text-align: center;">
                Click the button below to set a new password:
            </p>
            
            <!-- CTA Button -->
            <div style="text-align: center; margin-bottom: 32px;">
                <a href="{reset_link}" 
                   style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #14b8a6 100%); color: white; text-decoration: none; padding: 16px 48px; border-radius: 12px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 14px 0 rgba(16, 185, 129, 0.4);">
                    Reset Password
                </a>
            </div>
            
            <p style="color: #9ca3af; font-size: 14px; text-align: center; margin: 0 0 16px 0;">
                Or copy and paste this link into your browser:
            </p>
            
            <p style="color: #10b981; font-size: 14px; text-align: center; word-break: break-all; margin: 0 0 32px 0;">
                {reset_link}
            </p>
            
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 32px 0;">
            
            <p style="color: #9ca3af; font-size: 13px; text-align: center; margin: 0;">
                This link will expire in <strong>1 hour</strong>. If you didn't request a password reset, you can safely ignore this email.
            </p>
        </div>
        
        <!-- Footer -->
        <div style="text-align: center; margin-top: 32px;">
            <p style="color: #9ca3af; font-size: 12px; margin: 0;">
                © 2026 Big Motion Studio. All rights reserved.
            </p>
            <p style="color: #9ca3af; font-size: 12px; margin: 8px 0 0 0;">
                Create viral short-form videos on autopilot.
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    return subject, html_body


def get_verification_email(verification_token: str, user_email: str) -> tuple[str, str]:
    """
    Generate email verification content.
    Returns: (subject, html_body)
    """
    verify_link = f"{FRONTEND_URL}/verify-email?token={verification_token}"
    
    subject = "Verify Your Email - Big Motion Studio"
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f0fdf4;">
    <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
        <!-- Header -->
        <div style="text-align: center; margin-bottom: 32px;">
            <div style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #14b8a6 100%); padding: 16px; border-radius: 16px; margin-bottom: 16px;">
                <span style="font-size: 32px;">🎬</span>
            </div>
            <h1 style="color: #059669; margin: 0; font-size: 24px; font-weight: bold;">Big Motion Studio</h1>
        </div>
        
        <!-- Card -->
        <div style="background: white; border-radius: 16px; padding: 40px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            <h2 style="color: #1f2937; margin: 0 0 16px 0; font-size: 20px; text-align: center;">Welcome! Verify Your Email</h2>
            
            <p style="color: #6b7280; font-size: 16px; line-height: 1.6; margin: 0 0 24px 0; text-align: center;">
                Thanks for signing up! Please verify your email address <strong>{user_email}</strong> to get started.
            </p>
            
            <!-- CTA Button -->
            <div style="text-align: center; margin-bottom: 32px;">
                <a href="{verify_link}" 
                   style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #14b8a6 100%); color: white; text-decoration: none; padding: 16px 48px; border-radius: 12px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 14px 0 rgba(16, 185, 129, 0.4);">
                    Verify Email
                </a>
            </div>
            
            <p style="color: #9ca3af; font-size: 14px; text-align: center; margin: 0 0 16px 0;">
                Or copy and paste this link into your browser:
            </p>
            
            <p style="color: #10b981; font-size: 14px; text-align: center; word-break: break-all; margin: 0;">
                {verify_link}
            </p>
        </div>
        
        <!-- Footer -->
        <div style="text-align: center; margin-top: 32px;">
            <p style="color: #9ca3af; font-size: 12px; margin: 0;">
                © 2026 Big Motion Studio. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    return subject, html_body


# =============================================================================
# Email Sending Functions
# =============================================================================

async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None
) -> bool:
    """
    Send an email using Resend.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_body: HTML content of the email
        text_body: Plain text version (optional)
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        if not RESEND_API_KEY:
            logger.error("RESEND_API_KEY not configured")
            return False
        
        logger.info(f"Sending email to {to_email}: {subject}")
        
        # Build email params
        params = {
            "from": f"Big Motion Studio <{EMAIL_FROM}>",
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }
        
        # Add plain text if provided
        if text_body:
            params["text"] = text_body
        
        # Send email via Resend
        response = resend.Emails.send(params)
        
        logger.info(f"✅ Email sent successfully to {to_email} (ID: {response.get('id', 'unknown')})")
        return True
        
    except resend.exceptions.ResendError as e:
        logger.error(f"Resend error sending email to {to_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {e}")
        return False


async def send_reset_email(to_email: str, reset_token: str) -> bool:
    """
    Send password reset email.
    
    Args:
        to_email: User's email address
        reset_token: Password reset token
    
    Returns:
        True if sent successfully
    """
    subject, html_body = get_reset_password_email(reset_token, to_email)
    
    text_body = f"""
Reset Your Password - Big Motion Studio

We received a request to reset the password for your account.

Click this link to reset your password:
{FRONTEND_URL}/reset-password?token={reset_token}

This link will expire in 1 hour.

If you didn't request a password reset, you can safely ignore this email.

© 2026 Big Motion Studio
"""
    
    return await send_email(to_email, subject, html_body, text_body)


async def send_verification_email(to_email: str, verification_token: str) -> bool:
    """
    Send email verification email.
    
    Args:
        to_email: User's email address
        verification_token: Email verification token
    
    Returns:
        True if sent successfully
    """
    subject, html_body = get_verification_email(verification_token, to_email)
    
    text_body = f"""
Verify Your Email - Big Motion Studio

Thanks for signing up! Please verify your email address to get started.

Click this link to verify:
{FRONTEND_URL}/verify-email?token={verification_token}

© 2026 Big Motion Studio
"""
    
    return await send_email(to_email, subject, html_body, text_body)
