# CREDENTIALS FOR APIs

import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_SID = os.getenv('TWILIO_SID')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
EMAIL = os.getenv('EMAIL')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
