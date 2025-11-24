# utils/notifications.py
from .firebase_init import *
from firebase_admin import messaging

def send_fcm_notification(token: str, title: str, body: str, data: dict = None):
    """
    Send a Firebase Cloud Messaging notification to a specific device token.

    Args:
        token (str): FCM device token.
        title (str): Notification title.
        body (str): Notification body text.
        data (dict, optional): Optional data payload.

    Returns:
        str: Message ID if sent successfully, None otherwise.
    """
    try:
        message = messaging.Message(
            token=token,
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
        )

        response = messaging.send(message)
        print(f"✅ FCM sent successfully: {response}")
        return response

    except Exception as e:
        print(f"❌ Failed to send FCM notification: {e}")
        return None
