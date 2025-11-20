from rest_framework import serializers
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser


# -------------------------------
# Full User Serializer (includes followers + following + status)
# -------------------------------
class UserSerializer(serializers.ModelSerializer):
    followers = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    following = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    profile_picture = serializers.SerializerMethodField()
    banner_image = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    is_online = serializers.BooleanField(read_only=True)       # ✅ Added
    last_seen = serializers.DateTimeField(read_only=True)      # ✅ Added

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
            "following",
            "is_following",
            "is_online",   # ✅
            "last_seen",   # ✅
            "created_at",
        ]
        read_only_fields = [
            "created_at",
            "followers",
            "following",
            "is_following",
            "is_online",
            "last_seen",
        ]

    def get_profile_picture(self, obj):
        request = self.context.get("request")
        if obj.profile_picture:
            try:
                return request.build_absolute_uri(obj.profile_picture.url)
            except Exception:
                return obj.profile_picture.url
        return None

    def get_banner_image(self, obj):
        request = self.context.get("request")
        if obj.banner_image:
            try:
                return request.build_absolute_uri(obj.banner_image.url)
            except Exception:
                return obj.banner_image.url
        return None

    def get_is_following(self, obj):
        """Check if the current authenticated user follows this user."""
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            return request.user in obj.followers.all()
        return False


# -------------------------------
# Email Signup
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
        user.username = user.email.split("@")[0]
        user.set_password(password)
        user.is_email_verified = True
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
                message=(
                    f"Hello {self.user.first_name or self.user.username},\n\n"
                    f"Your password reset code is: {code}\nIt expires in 15 minutes."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.user.email],
                fail_silently=True,
            )
        return {
            "detail": "If an account with that email exists, a reset code has been sent."
        }


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
            raise serializers.ValidationError(
                {"email": "Invalid email or reset code."}
            )

        if not self.user.verify_password_reset_code(data["code"]):
            raise serializers.ValidationError(
                {"code": "Invalid or expired reset code."}
            )

        return data

    def save(self):
        self.user.set_password(self.validated_data["new_password"])
        self.user.clear_password_reset_code()
        self.user.save()
        return {"detail": "Password reset successful."}


# -------------------------------
# Profile Update Serializer
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
        profile_picture = validated_data.pop("profile_picture", None)
        banner_image = validated_data.pop("banner_image", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if profile_picture is not None:
            instance.profile_picture = profile_picture
        if banner_image is not None:
            instance.banner_image = banner_image

        instance.save()
        return instance
