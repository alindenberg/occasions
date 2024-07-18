import requests
from config import get_settings


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