from rest_framework import serializers
from django.contrib.auth import get_user_model
from posts.models import Post, PostImage
from comments.models import Comment
from .models import Notification, FCMDevice

User = get_user_model()


# -------------------------------
# User Serializer (Mini)
# -------------------------------
class UserMiniSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "profile_picture"]

    def get_profile_picture(self, instance):
        request = self.context.get("request")
        if instance.profile_picture and request:
            return request.build_absolute_uri(instance.profile_picture.url)
        return None


# -------------------------------
# PostImage Serializer
# -------------------------------
class PostImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = PostImage
        fields = ["id", "image"]

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


# -------------------------------
# Post (Mini) Serializer
# -------------------------------
class PostMiniSerializer(serializers.ModelSerializer):
    images = PostImageSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ["id", "content", "images"]


# -------------------------------
# Comment (Mini) Serializer
# -------------------------------
class CommentMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "content"]


# -------------------------------
# Notification Serializer
# -------------------------------
class NotificationSerializer(serializers.ModelSerializer):
    from_user = UserMiniSerializer(read_only=True)
    to_user = UserMiniSerializer(read_only=True)
    post = PostMiniSerializer(read_only=True)
    comment = CommentMiniSerializer(read_only=True)
    message = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "from_user",
            "to_user",
            "notification_type",
            "post",
            "comment",
            "message",
            "is_read",
            "created_at",
        ]

    def get_message(self, obj):
        username = obj.from_user.username if obj.from_user else "Someone"

        if obj.notification_type == "like":
            return f"{username} liked your post."
        elif obj.notification_type == "comment":
            if obj.comment:
                content_preview = obj.comment.content[:30]
                return f"{username} commented: {content_preview}"
            return f"{username} commented on your post."
        elif obj.notification_type == "follow":
            return f"{username} started following you."
        return "You have a new notification."


# -------------------------------
# FCM Device Serializer
# -------------------------------
class FCMDeviceSerializer(serializers.ModelSerializer):
    token = serializers.CharField(
        max_length=512,
        required=True,
    )

    class Meta:
        model = FCMDevice
        fields = ["token"]

    def create(self, validated_data):
        token = validated_data["token"]
        user = self.context["request"].user

        # Idempotent creation/updating
        device, created = FCMDevice.objects.get_or_create(
            token=token,
            defaults={"user": user}
        )

        # Update user if token already exists
        if not created and device.user != user:
            device.user = user
            device.save()

        return device
