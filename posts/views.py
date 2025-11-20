from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .models import Post, Hashtag
from .serializers import PostSerializer, PostCreateSerializer


# -------------------------------
# List all posts (feed)
# -------------------------------
class PostListView(generics.ListAPIView):
    serializer_class = PostSerializer
    queryset = Post.objects.all().order_by("-created_at")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


# -------------------------------
# Retrieve a single post
# -------------------------------
class PostDetailView(generics.RetrieveAPIView):
    serializer_class = PostSerializer
    queryset = Post.objects.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


# -------------------------------
# Create a new post (multi-image, hashtags)
# -------------------------------
class PostCreateView(generics.CreateAPIView):
    serializer_class = PostCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


# -------------------------------
# Like / Unlike a post
# -------------------------------
class PostLikeToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        user = request.user

        if user in post.likes.all():
            post.likes.remove(user)
            action = "unliked"
        else:
            post.likes.add(user)
            action = "liked"

        return Response(
            {"detail": f"Post successfully {action}.", "likes_count": post.likes.count()}
        )


# -------------------------------
# Delete a post (owner only)
# -------------------------------
class PostDeleteView(generics.DestroyAPIView):
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You can only delete your own posts.")
        super().perform_destroy(instance)


# -------------------------------
# Get all posts for a specific username
# -------------------------------
class UserPostsView(generics.ListAPIView):
    serializer_class = PostSerializer

    def get_queryset(self):
        username = self.kwargs.get("username")
        return Post.objects.filter(user__username=username).order_by("-created_at")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


# -------------------------------
# ✅ New: Get all posts for a specific hashtag
# -------------------------------
class HashtagPostsView(generics.ListAPIView):
    serializer_class = PostSerializer

    def get_queryset(self):
        hashtag_name = self.kwargs.get("name").lower()
        hashtag = get_object_or_404(Hashtag, name=hashtag_name)
        return hashtag.posts.all().order_by("-created_at")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
