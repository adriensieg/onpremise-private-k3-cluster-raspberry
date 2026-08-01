import os

# --- Server ---
PORT = int(os.getenv("PORT", "8000"))
APP_BASE_URL = os.getenv("APP_BASE_URL", "https://techie.devailab.work")

# --- API credentials (from env / k8s secrets) ---
GOOGLE_API_KEY      = os.getenv("GOOGLE_API_KEY", "")
TWILIO_ACCOUNT_SID  = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN   = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

# --- API access control ---
API_KEY = os.getenv("API_KEY", "")  # bearer token callers must present

# --- Single predefined technician ---
TECHNICIAN_PHONE = os.getenv("TECHNICIAN_PHONE", "+17734058426")