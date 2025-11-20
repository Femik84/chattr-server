# search/views.py
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination

from posts.models import Post
from posts.serializers import PostSerializer
from users.serializers import UserSerializer

User = get_user_model()


# Custom paginator for posts only
class PostPagination(PageNumberPagination):
    page_size = 20                # default posts per page
    page_size_query_param = "page_size"
    max_page_size = 50


class SearchView(APIView):
    """
    Search API

    Pagination:
        - Users ❌ not paginated
        - Posts ✔ paginated

    GET /api/search/?q=something&page=2
    """

    permission_classes = [AllowAny]

    MAX_USER_RESULTS = 20  # users are still capped, not paginated

    def get(self, request, format=None):
        q = request.query_params.get("q", "")
        q = (q or "").strip()

        if not q:
            return Response(
                {"detail": "Query parameter `q` is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------
        # 🔎 Search Users (not paginated)
        # -----------------------------
        user_filter = (
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
        )

        users_qs = User.objects.filter(user_filter).distinct()[: self.MAX_USER_RESULTS]

        # -----------------------------
        # 🔎 Search Posts (paginated)
        # -----------------------------
        post_filter = (
            Q(content__icontains=q)
            | Q(user__username__icontains=q)
            | Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
        )

        posts_qs = (
            Post.objects.filter(post_filter)
            .select_related("user")
            .prefetch_related("images", "likes")
            .distinct()
            .order_by("-created_at")
        )

        # Apply pagination to posts only
        paginator = PostPagination()
        paginated_posts = paginator.paginate_queryset(posts_qs, request)

        context = {"request": request}
        users_data = UserSerializer(users_qs, many=True, context=context).data
        posts_data = PostSerializer(paginated_posts, many=True, context=context).data

        # Return DRF paginated response for posts,
        # but also include the users list & query string.
        return paginator.get_paginated_response(
            {
                "query": q,
                "users": users_data,
                "posts": posts_data,
            }
        )
