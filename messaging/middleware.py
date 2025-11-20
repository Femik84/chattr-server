from urllib.parse import parse_qs
import traceback

class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        from rest_framework_simplejwt.tokens import UntypedToken
        from django.contrib.auth import get_user_model
        from django.db import close_old_connections
        from asgiref.sync import sync_to_async
        import jwt

        close_old_connections()

        # Get headers
        headers = dict(scope.get("headers", []))
        token = None

        if b"authorization" in headers:
            try:
                auth_header = headers[b"authorization"].decode()
                if auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
            except Exception as e:
                print("Error reading Authorization header:", e)
                traceback.print_exc()
                token = None

        # Also check query string
        if not token:
            try:
                query_params = parse_qs(scope.get("query_string", b"").decode())
                token = query_params.get("token", [None])[0]
            except Exception as e:
                print("Error parsing query string:", e)
                traceback.print_exc()
                token = None

        scope["user"] = None

        if token:
            try:
                print("Token received:", token)
                # Verify signature and validity
                UntypedToken(token)
                decoded = jwt.decode(token, options={"verify_signature": False})
                print("Decoded JWT payload:", decoded)

                user_id = decoded.get("user_id")
                if user_id is None:
                    raise ValueError("user_id not found in token payload")

                User = get_user_model()
                scope["user"] = await sync_to_async(User.objects.get)(id=user_id)
                print(f"User {scope['user']} attached to scope")
            except Exception as e:
                print("JWT validation error:", e)
                traceback.print_exc()
                scope["user"] = None
        else:
            print("No token found in headers or query string")

        return await self.inner(scope, receive, send)
