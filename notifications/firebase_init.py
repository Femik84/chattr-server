import os
from dotenv import load_dotenv  
import firebase_admin
from firebase_admin import credentials

# Load .env file manually
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))  # <-- ensures env vars are loaded

# Check private key exists
private_key = os.getenv("FIREBASE_PRIVATE_KEY")
if not private_key:
    raise ValueError("FIREBASE_PRIVATE_KEY is not set in your .env file")

# Initialize Firebase Admin only once
if not firebase_admin._apps:
    firebase_creds = {
        "type": os.getenv("FIREBASE_TYPE"),
        "project_id": os.getenv("FIREBASE_PROJECT_ID"),
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": private_key.replace("\\n", "\n"),
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "client_id": os.getenv("FIREBASE_CLIENT_ID"),
        "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
        "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
        "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
    }

    cred = credentials.Certificate(firebase_creds)
    firebase_admin.initialize_app(cred)
    print("✅ Firebase Admin initialized successfully")
