from rest_framework import serializers
from .models import Post, PostImage, Hashtag
from comments.models import Comment
from comments.serializers import CommentSerializer
from users.serializers import UserSerializer  


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
# Post Serializer (for reading)
# -------------------------------
class PostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    likes_count = serializers.IntegerField(source="likes.count", read_only=True)
    is_liked = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    hashtags = HashtagSerializer(many=True, read_only=True)  # 🔹 include hashtags

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "content",
            "images",
            "likes_count",
            "is_liked",
            "comments",
            "hashtags",  # 🔹 new field
            "created_at",
        ]

    def get_is_liked(self, obj):
        user = self.context.get("request").user
        return user in obj.likes.all() if user.is_authenticated else False

    def get_comments(self, obj):
        comments = Comment.objects.filter(post=obj).order_by("-created_at")
        return CommentSerializer(comments, many=True, context=self.context).data


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
            hashtag, created = Hashtag.objects.get_or_create(name=tag_name.lower())
            post.hashtags.add(hashtag)

        return post
