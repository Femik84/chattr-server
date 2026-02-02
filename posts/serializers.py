from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Post, PostImage, Hashtag
from comments.serializers import CommentSerializer
from users.serializers import UserSerializer  # ensure this serializer is lightweight for lists

User = get_user_model()


# ------------------------------- 
# PostImage Serializer
# -------------------------------
class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ["id", "image"]


# -------------------------------
# Hashtag Serializer
# -------------------------------
class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ["id", "name"]


# -------------------------------
# Post Serializer used for list endpoints (lightweight)
# -------------------------------
class PostListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    hashtags = HashtagSerializer(many=True, read_only=True)

    # annotated fields (added in queryset) or fallback
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "content",
            "images",
            "likes_count",
            "comments_count",
            "is_liked",
            "hashtags",
            "created_at",
        ]

    def get_is_liked(self, obj):
        request = self.context.get("request", None)
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        # Try to read prefetched likes (fast, no DB hit)
        prefetched = getattr(obj, "_prefetched_objects_cache", {}).get("likes", None)
        if prefetched is not None:
            return any(u.id == user.id for u in prefetched)

        # Fallback to DB hit (only when necessary)
        return obj.likes.filter(id=user.id).exists()


# -------------------------------
# Post Serializer used for detail endpoint (includes comments)
# -------------------------------
class PostDetailSerializer(PostListSerializer):
    comments = CommentSerializer(many=True, read_only=True)

    class Meta(PostListSerializer.Meta):
        # Keep all fields from list serializer and add comments
        fields = PostListSerializer.Meta.fields + ["comments"]


# -------------------------------
# Post Create Serializer (for writing)
# -------------------------------
class PostCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    hashtags = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        help_text="Optional list of hashtags (without #)"
    )

    class Meta:
        model = Post
        fields = ["content", "images", "hashtags"]

    def create(self, validated_data):
        images_data = validated_data.pop("images", [])
        hashtags_data = validated_data.pop("hashtags", [])
        user = self.context["request"].user
        post = Post.objects.create(user=user, **validated_data)

        # Handle images
        for image in images_data:
            PostImage.objects.create(post=post, image=image)

        # Handle hashtags
        for tag_name in hashtags_data:
            hashtag, _created = Hashtag.objects.get_or_create(name=tag_name.lower())
            post.hashtags.add(hashtag)

        return post


# -------------------------------
# Compatibility alias
# -------------------------------
# Some code (e.g. search.views) still imports `PostSerializer`. Provide an alias
# so existing imports keep working. Point it to the detail serializer so callers
# get the richer representation.
PostSerializer = PostDetailSerializer