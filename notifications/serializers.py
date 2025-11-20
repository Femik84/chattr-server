from rest_framework import serializers
from django.contrib.auth import get_user_model
from posts.models import Post, PostImage
from comments.models import Comment
from .models import Notification

User = get_user_model()


# -------------------------------
# User Serializer (Mini)
# -------------------------------
class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "profile_picture"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")

        if instance.profile_picture and request:
            data["profile_picture"] = request.build_absolute_uri(instance.profile_picture.url)
        return data


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
        username = obj.from_user.username

        if obj.notification_type == "like":
            return f"{username} liked your post."
        elif obj.notification_type == "comment":
            if obj.comment:
                return f"{username} commented: {obj.comment.content}"
            return f"{username} commented on your post."
        elif obj.notification_type == "follow":
            return f"{username} started following you."
        return "You have a new notification."
