from django.shortcuts import get_object_or_404
from django.db.models import Count, Prefetch
from django.contrib.auth import get_user_model

from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import Post, Hashtag
from .serializers import (
    PostListSerializer,
    PostDetailSerializer,
    PostCreateSerializer,
)

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50


# -------------------------------
# List all posts (feed) -- optimized
# -------------------------------
class PostListView(generics.ListAPIView):
    serializer_class = PostListSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = (
            Post.objects.select_related("user")
            .prefetch_related(
                "images",                # reverse FK to PostImage
                "hashtags",              # M2M
                Prefetch("likes", queryset=User.objects.only("id")),  # prefetch minimal user fields
            )
            .annotate(
                likes_count=Count("likes", distinct=True),
                comments_count=Count("comments", distinct=True),
            )
            .order_by("-created_at")
        )
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


# -------------------------------
# Retrieve a single post (detail) - prefetch comments for the detail view
# -------------------------------
class PostDetailView(generics.RetrieveAPIView):
    serializer_class = PostDetailSerializer

    def get_queryset(self):
        return (
            Post.objects.select_related("user")
            .prefetch_related(
                "images",
                "hashtags",
                Prefetch("likes", queryset=User.objects.only("id")),
                Prefetch("comments__user"),  # prefetch comment user for serializer
            )
            .annotate(
                likes_count=Count("likes", distinct=True),
                comments_count=Count("comments", distinct=True),
            )
        )

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
# Get all posts for a specific username (optimized)
# -------------------------------
class UserPostsView(generics.ListAPIView):
    serializer_class = PostListSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        username = self.kwargs.get("username")
        return (
            Post.objects.filter(user__username=username)
            .select_related("user")
            .prefetch_related(
                "images",
                "hashtags",
                Prefetch("likes", queryset=User.objects.only("id")),
            )
            .annotate(
                likes_count=Count("likes", distinct=True),
                comments_count=Count("comments", distinct=True),
            )
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


# -------------------------------
# Get all posts for a specific hashtag (optimized)
# -------------------------------
class HashtagPostsView(generics.ListAPIView):
    serializer_class = PostListSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        hashtag_name = self.kwargs.get("name").lower()
        hashtag = get_object_or_404(Hashtag, name=hashtag_name)
        return (
            hashtag.posts.all()
            .select_related("user")
            .prefetch_related(
                "images",
                Prefetch("likes", queryset=User.objects.only("id")),
            )
            .annotate(
                likes_count=Count("likes", distinct=True),
                comments_count=Count("comments", distinct=True),
            )
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context