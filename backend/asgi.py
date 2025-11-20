import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Load Django first
django_asgi_app = get_asgi_application()

# Now safe to import routing AFTER Django is loaded
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from messaging.routing import websocket_urlpatterns
from messaging.middleware import JWTAuthMiddleware


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    )
})
