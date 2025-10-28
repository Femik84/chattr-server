from rest_framework import serializers
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser


# -------------------------------
# Basic User Serializer (read-only followers)
# -------------------------------
class UserSerializer(serializers.ModelSerializer):
    followers = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "profile_picture",
            "banner_image",
            "bio",
            "location",
            "followers",
            "created_at",
        ]
        read_only_fields = ["created_at", "followers"]


# -------------------------------
# Email Signup (instant, no verification code)
# -------------------------------
class EmailSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = [
            "email",
            "first_name",
            "last_name",
            "password",
            "profile_picture",
            "banner_image",
            "bio",
            "location",
        ]

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = CustomUser.objects.create(**validated_data)
        user.username = validated_data["email"]  # or generate a custom username
        user.set_password(password)
        user.is_email_verified = True  # mark as verified
        user.save()
        return user


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
            send_mail(
                subject="Your Password Reset Code",
                message=f"Hello {self.user.first_name or self.user.username},\n\n"
                        f"Your password reset code is: {code}\nIt expires in 15 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.user.email],
                fail_silently=True,
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
            "username",
            "first_name",
            "last_name",
            "profile_picture",
            "banner_image",
            "bio",
            "location",
        ]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
