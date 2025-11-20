from django.urls import path
from .views import (
    PostListView,
    PostDetailView,
    PostCreateView,
    PostLikeToggleView,
    PostDeleteView,
    UserPostsView,
    HashtagPostsView,  
)

urlpatterns = [
    # List all posts (feed)
    path("", PostListView.as_view(), name="post-list"),

    # Get all posts by a specific user
    path("users/<str:username>/posts/", UserPostsView.as_view(), name="user-posts"),

    # Create a new post
    path("create/", PostCreateView.as_view(), name="post-create"),

    # Retrieve a single post
    path("<int:pk>/", PostDetailView.as_view(), name="post-detail"),

    # Like / Unlike a post
    path("<int:post_id>/like/", PostLikeToggleView.as_view(), name="post-like-toggle"),

    # Delete a post
    path("<int:pk>/delete/", PostDeleteView.as_view(), name="post-delete"),

    # 🔹 Get all posts for a specific hashtag
    path("hashtags/<str:name>/posts/", HashtagPostsView.as_view(), name="hashtag-posts"),
]
