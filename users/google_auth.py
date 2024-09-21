import logging
from google.oauth2 import id_token
from google.auth.transport import requests
from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def verify_google_token(token: str):
    try:
        # Decode without verification to check the payload
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_CLIENT_ID)
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        return idinfo
    except Exception as e:
        logger.error(f"Error verifying Google token: {e}")
        return None
