import requests
from config import get_settings


settings = get_settings()


class MailService:
    def send_email(self, recipient_email, subject, body):
        settings = get_settings()
        requests.post(
            "https://api.mailgun.net/v3/mg.occasionalert.me/messages",
            auth=("api", settings.MAILGUN_API_KEY),
            data={
                "from": "Occasion Alerts <mailgun@mg.occasionalert.me>",
                "to": [recipient_email],
                "subject": subject,
                "text": body
            }
        )

    def send_verification_email(self, recipient_email, verification_url):
        subject = "Verify your email"
        body = f"Click the link to verify your email: {verification_url}"
        self.send_email(recipient_email, subject, body)

    def send_password_reset_email(self, recipient_email, reset_hash):
        reset_link = f"{settings.NEXT_PUBLIC_URL}/account/reset-password?hash={reset_hash}"

        subject = "Reset your password"
        body = f"Click the link to reset your password: {reset_link}"
        self.send_email(recipient_email, subject, body)