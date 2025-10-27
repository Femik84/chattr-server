from rest_framework import serializers
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.hashers import make_password
import random
from datetime import timedelta
from .models import CustomUser, EmailVerificationRequest
from .email import send_email  # import the helper


# -------------------------------
# Basic User Serializer
# -------------------------------
class UserSerializer(serializers.ModelSerializer):
    followers = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id", "username", "first_name", "last_name", "email",
            "profile_picture", "banner_image", "bio", "location",
            "followers", "created_at"
        ]
        read_only_fields = ["created_at", "followers"]


# -------------------------------
# Signup Step 1 — Send Verification Code
# -------------------------------
class EmailSignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    banner_image = serializers.ImageField(required=False, allow_null=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def save(self):
        email = self.validated_data["email"]
        code = str(random.randint(100000, 999999))
        password_hash = make_password(self.validated_data["password"])
        expires_at = timezone.now() + timedelta(minutes=15)

        # Remove old verification requests
        EmailVerificationRequest.objects.filter(email=email).delete()

        EmailVerificationRequest.objects.create(
            email=email,
            password_hash=password_hash,
            first_name=self.validated_data.get("first_name"),
            last_name=self.validated_data.get("last_name", ""),
            profile_picture=self.validated_data.get("profile_picture"),
            banner_image=self.validated_data.get("banner_image"),
            bio=self.validated_data.get("bio", ""),
            location=self.validated_data.get("location", ""),
            verification_code=code,
            expires_at=expires_at,
        )

        # Send verification email
        send_email(
            to_email=email,
            subject="Verify your email",
            message=f"Your verification code is: {code}"
        )

        return {"detail": "Verification code sent to email."}


# -------------------------------
# Signup Step 2 — Verify Code and Create User
# -------------------------------
class EmailVerificationConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        try:
            self.request_entry = EmailVerificationRequest.objects.get(email=data["email"])
        except EmailVerificationRequest.DoesNotExist:
            raise serializers.ValidationError({"email": "No verification request found for this email."})

        if self.request_entry.is_expired():
            raise serializers.ValidationError({"code": "Verification code has expired."})

        if self.request_entry.verification_code != data["code"]:
            raise serializers.ValidationError({"code": "Invalid verification code."})

        return data

    def save(self):
        entry = self.request_entry
        user = CustomUser.objects.create(
            email=entry.email,
            username=entry.email,
            first_name=entry.first_name,
            last_name=entry.last_name,
            profile_picture=entry.profile_picture,
            banner_image=entry.banner_image,
            bio=entry.bio,
            location=entry.location,
            is_email_verified=True,
        )
        user.password = entry.password_hash
        user.save()
        entry.delete()
        return {"detail": "Email verified successfully. Account created."}


# -------------------------------
# Password Reset Request
# -------------------------------
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            self.user = CustomUser.objects.get(email__iexact=value)
        except CustomUser.DoesNotExist:
            self.user = None
        return value

    def save(self):
        if self.user:
            code = self.user.create_password_reset_code()
            send_email(
                to_email=self.user.email,
                subject="Your Password Reset Code",
                message=f"Hello {self.user.first_name or self.user.username},\n\n"
                        f"Your password reset code is: {code}\nIt expires in 15 minutes."
            )
        return {"detail": "If an account with that email exists, a reset code has been sent."}


# -------------------------------
# Password Reset Confirmation
# -------------------------------
class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, data):
        try:
            self.user = CustomUser.objects.get(email__iexact=data["email"])
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({"email": "Invalid email or reset code."})

        if not self.user.verify_password_reset_code(data["code"]):
            raise serializers.ValidationError({"code": "Invalid or expired reset code."})

        return data

    def save(self):
        self.user.set_password(self.validated_data["new_password"])
        self.user.clear_password_reset_code()
        self.user.save()
        return {"detail": "Password reset successful."}


# -------------------------------
# Update Profile Serializer
# -------------------------------
class UserUpdateSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    banner_image = serializers.ImageField(required=False, allow_null=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = [
            "username", "first_name", "last_name",
            "profile_picture", "banner_image", "bio", "location"
        ]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
