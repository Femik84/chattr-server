from rest_framework import serializers
from django.conf import settings
from .models import Comment
from posts.models import Post

User = settings.AUTH_USER_MODEL


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()  # new field

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "post",
            "content",
            "likes_count",
            "is_liked",
            "created_at",
            "updated_at",
            "parent",
            "replies",  # include replies
        ]

    def get_user(self, obj):
        user_obj = obj.user
        request = self.context.get("request")
        fallback_avatar = "https://cdn-icons-png.flaticon.com/512/149/149071.png"

        profile_picture_url = None
        if hasattr(user_obj, "profile_picture") and user_obj.profile_picture:
            try:
                profile_picture_url = request.build_absolute_uri(user_obj.profile_picture.url)
            except Exception:
                profile_picture_url = None

        return {
            "id": user_obj.id,
            "username": getattr(user_obj, "username", None),
            "email": getattr(user_obj, "email", None),
            "first_name": getattr(user_obj, "first_name", ""),
            "last_name": getattr(user_obj, "last_name", ""),
            "profile_picture": profile_picture_url or fallback_avatar,
        }

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        user = self.context.get("request").user
        if user and user.is_authenticated:
            return obj.likes.filter(id=user.id).exists()
        return False

    def get_replies(self, obj):
        # recursively serialize child comments
        replies_qs = obj.replies.all().order_by("created_at")  # oldest first for replies
        return CommentSerializer(replies_qs, many=True, context=self.context).data


class CommentCreateUpdateSerializer(serializers.ModelSerializer):
    """Handles comment creation and update, now supports parent replies."""

    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Comment
        fields = ["content", "parent"]

    def create(self, validated_data):
        request = self.context.get("request")
        post_id = self.context.get("post_id")
        user = request.user

        parent = validated_data.pop("parent", None)

        if not post_id:
            raise serializers.ValidationError({"post": "Post ID is required."})

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise serializers.ValidationError({"post": "Post not found."})

        # Ensure parent comment belongs to the same post
        if parent and parent.post_id != post.id:
            raise serializers.ValidationError({"parent": "Parent comment must belong to the same post"})

        return Comment.objects.create(
            user=user,
            post=post,
            content=validated_data["content"],
            parent=parent
        )

    def update(self, instance, validated_data):
        instance.content = validated_data.get("content", instance.content)
        instance.save()
        return instance
