from django.urls import path
from .views import (
    PostCommentListCreateView,
    CommentDetailView,
    CommentLikeToggleView,
)

urlpatterns = [
    # List all comments for a post + create new comment
    path("posts/<int:post_id>/comments/", PostCommentListCreateView.as_view(), name="post-comments"),

    # Retrieve, update, delete single comment
    path("comments/<int:comment_id>/", CommentDetailView.as_view(), name="comment-detail"),

    # Like / Unlike comment
    path("comments/<int:comment_id>/like/", CommentLikeToggleView.as_view(), name="comment-like-toggle"),
]
