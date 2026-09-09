import resend

from app.core.config import settings


def send_password_reset_email(
    recipient_email: str,
    reset_url: str,
) -> None:
    if not settings.resend_api_key:
        raise RuntimeError("RESEND_API_KEY is not configured.")

    resend.api_key = settings.resend_api_key

    resend.Emails.send(
        {
            "from": "DigiBills <onboarding@resend.dev>",
            "to": [recipient_email],
            "subject": "Reset your DigiBills password",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 32px;">
                <h2 style="color: #7352D6;">DigiBills</h2>

                <h1>Reset Your Password</h1>

                <p>
                    We received a request to reset the password for your DigiBills account.
                </p>

                <p>
                    Click the button below to create a new password.
                </p>

                <p style="margin: 32px 0;">
                    <a
                        href="{reset_url}"
                        style="
                            display: inline-block;
                            background: #7352D6;
                            color: #ffffff;
                            text-decoration: none;
                            padding: 14px 24px;
                            border-radius: 8px;
                            font-weight: 600;
                        "
                    >
                        Reset Password
                    </a>
                </p>

                <p>
                    This password reset link will expire in 30 minutes.
                </p>

                <p style="color: #666666; font-size: 13px;">
                    If you did not request a password reset, you can safely ignore this email.
                </p>
            </div>
            """,
        }
    )
