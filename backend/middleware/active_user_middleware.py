# your_project/middleware/active_user_middleware.py
from django.utils import timezone
from datetime import timedelta

class ActiveUserMiddleware:
    """
    Middleware that updates a user's `last_seen` and `is_online` status
    whenever they make an authenticated request.

    Add this AFTER authentication middleware in settings.py.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            now = timezone.now()
            # If user inactive for >5 minutes, consider them "back online"
            if not user.is_online or (user.last_seen and now - user.last_seen > timedelta(minutes=5)):
                user.is_online = True
                user.last_seen = now
                user.save(update_fields=["is_online", "last_seen"])
            else:
                # Just update the timestamp (light update)
                user.last_seen = now
                user.save(update_fields=["last_seen"])

        return response
