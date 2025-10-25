from django.contrib.auth import get_user_model, authenticate
from django.core.mail import send_mail
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    UserSerializer,
    UserUpdateSerializer,
    EmailSignupSerializer,
    EmailVerificationConfirmSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from .models import EmailVerificationRequest

User = get_user_model()
GOOGLE_CLIENT_ID = "158085473947-ue7no55fodi835t0f9lekld8nkms9ip9.apps.googleusercontent.com"


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

            refresh = RefreshToken.for_user(user)
            serializer = UserSerializer(user)
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
# EMAIL SIGNUP (Step 1)
# -----------------------------
class EmailSignupView(APIView):
    """
    Collect user data and send verification code.
    Creates a temporary EmailVerificationRequest entry (not the real user yet).
    """
    def post(self, request):
        serializer = EmailSignupSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------
# EMAIL VERIFICATION (Step 2)
# -----------------------------
class VerifyEmailView(APIView):
    """
    Verify the email and create the user after successful code validation.
    """
    def post(self, request):
        serializer = EmailVerificationConfirmSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------
# EMAIL LOGIN
# -----------------------------
class EmailLoginView(APIView):
    """Log in with email and password (only if email verified)."""

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"detail": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=email, password=password)
        if not user:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_email_verified:
            return Response({"detail": "Email not verified."}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        serializer = UserSerializer(user)
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

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
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
