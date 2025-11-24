from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from .serializers import (
    UserSerializer,
    UserUpdateSerializer,
    EmailSignupSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

from notifications.models import FCMDevice  # <<-- ensure this import points to your notifications app

User = get_user_model()
GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID


def attach_fcm_to_user_if_provided(request, user):
    """
    If client sent `fcm_token` in request.data, attach it to the provided user
    (idempotent — updates owner if token already existed).
    """
    token = request.data.get("fcm_token") or request.data.get("fcmToken")
    if not token:
        return None

    device, created = FCMDevice.objects.get_or_create(token=token, defaults={"user": user})
    if not created and device.user != user:
        device.user = user
        device.save()
    return device


# -----------------------------
# GOOGLE AUTHENTICATION
# -----------------------------
class GoogleAuthView(APIView):
    """Sign up or log in using a Google account."""

    def post(self, request):
        token = request.data.get("id_token")
        if not token:
            return Response({"detail": "Missing id_token"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
            email = idinfo["email"]
            first_name = idinfo.get("given_name", "")
            last_name = idinfo.get("family_name", "")
            picture = idinfo.get("picture", "")
            username = email.split("@")[0]

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "profile_picture": picture,
                    "is_email_verified": True,
                },
            )

            # Attach device token if provided
            attach_fcm_to_user_if_provided(request, user)

            refresh = RefreshToken.for_user(user)
            serializer = UserSerializer(user, context={"request": request})
            return Response(
                {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except ValueError:
            return Response({"detail": "Invalid Google token"}, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------
# EMAIL SIGNUP
# -----------------------------
class EmailSignupView(APIView):
    """Register a new user immediately (no verification code)."""

    def post(self, request):
        serializer = EmailSignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_email_verified = True
            user.save()

            # Attach device token if provided
            attach_fcm_to_user_if_provided(request, user)

            refresh = RefreshToken.for_user(user)
            user_data = UserSerializer(user, context={"request": request}).data

            return Response(
                {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": user_data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------
# EMAIL LOGIN (email + password)
# -----------------------------
class EmailLoginView(APIView):
    """Log in with email and password (only if email verified)."""

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"detail": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({"detail": "Account disabled."}, status=status.HTTP_403_FORBIDDEN)

        if not user.is_email_verified:
            return Response({"detail": "Email not verified."}, status=status.HTTP_403_FORBIDDEN)

        # Attach device token if provided (idempotent)
        attach_fcm_to_user_if_provided(request, user)

        refresh = RefreshToken.for_user(user)
        serializer = UserSerializer(user, context={"request": request})
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# -----------------------------
# CURRENT USER PROFILE
# -----------------------------
class MeView(APIView):
    """Retrieve or update current user's profile."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # ✅ Allows file + text data

    def get(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            updated_user = UserSerializer(request.user, context={"request": request}).data
            return Response(updated_user, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------
# FOLLOW / UNFOLLOW USER
# -----------------------------
class FollowToggleView(APIView):
    """Follow or unfollow another user."""
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if target_user == request.user:
            return Response({"detail": "Cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)

        if request.user in target_user.followers.all():
            target_user.followers.remove(request.user)
            action = "unfollowed"
        else:
            target_user.followers.add(request.user)
            action = "followed"

        return Response({"detail": f"Successfully {action} user."}, status=status.HTTP_200_OK)


# -----------------------------
# PASSWORD RESET FLOW
# -----------------------------
class PasswordResetRequestView(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------
# LOGOUT (removes FCM token)
# -----------------------------
class LogoutView(APIView):
    """
    Logs out the user and removes FCM token(s) as requested.

    Expected request body (examples):
      { "refresh": "<refresh_token>", "fcm_token": "<device_fcm_token>" }
    Behavior:
      - If `fcm_token` provided: delete only that token (so a new user of same device can register it).
      - If `fcm_token` NOT provided: delete ALL FCMDevice records for this user (useful for sign out everywhere).
      - Blacklist the refresh token (if provided).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        fcm_token = request.data.get("fcm_token") or request.data.get("fcmToken")
        removed_count = 0

        if fcm_token:
            removed_count, _ = FCMDevice.objects.filter(token=fcm_token).delete()
        else:
            # No token provided → remove all tokens owned by this user.
            # Change to a different behavior if you prefer only client-specified tokens removed.
            removed_count, _ = FCMDevice.objects.filter(user=request.user).delete()

        # Blacklist refresh token if provided (SimpleJWT)
        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                # ignore errors but return info
                pass

        return Response(
            {
                "detail": "Logged out successfully.",
                "fcm_tokens_removed": removed_count,
            },
            status=status.HTTP_200_OK,
        )


# -----------------------------
# GET USER BY USERNAME
# -----------------------------
class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
