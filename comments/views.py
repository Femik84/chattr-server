from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404

from .models import Comment
from posts.models import Post
from .serializers import CommentSerializer, CommentCreateUpdateSerializer


# -------------------------------
# List + Create comments under a post (supports replies)
# -------------------------------
class PostCommentListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, post_id):
        """
        List top-level comments for a post.
        Replies are included recursively via serializer.
        """
        post = get_object_or_404(Post, id=post_id)
        top_level_comments = post.comments.filter(parent__isnull=True).order_by("-created_at")
        serializer = CommentSerializer(top_level_comments, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, post_id):
        """
        Create a new comment or a reply.
        If 'parent' is provided in request.data, it's treated as a reply.
        """
        serializer = CommentCreateUpdateSerializer(
            data=request.data,
            context={"request": request, "post_id": post_id}
        )
        if serializer.is_valid():
            comment = serializer.save()
            read_serializer = CommentSerializer(comment, context={"request": request})
            return Response(read_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# Retrieve, Update, Delete a comment or reply
# -------------------------------
class CommentDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, comment_id):
        return get_object_or_404(Comment, id=comment_id)

    def get(self, request, comment_id):
        """Retrieve a single comment (or reply)"""
        comment = self.get_object(comment_id)
        serializer = CommentSerializer(comment, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, comment_id):
        """Edit a comment (only owner can edit)"""
        comment = self.get_object(comment_id)
        if comment.user != request.user:
            return Response({"detail": "You do not have permission to edit this comment."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = CommentCreateUpdateSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            read_serializer = CommentSerializer(comment, context={"request": request})
            return Response(read_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, comment_id):
        """Delete a comment (only owner can delete)"""
        comment = self.get_object(comment_id)
        if comment.user != request.user:
            return Response({"detail": "You do not have permission to delete this comment."},
                            status=status.HTTP_403_FORBIDDEN)

        comment.delete()  # all replies will also be deleted due to CASCADE
        return Response({"detail": "Comment deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


# -------------------------------
# Like / Unlike a comment or reply
# -------------------------------
class CommentLikeToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        """Toggle like/unlike for a comment or reply"""
        comment = self.get_object(comment_id)
        user = request.user

        if user in comment.likes.all():
            comment.likes.remove(user)
            action = "unliked"
        else:
            comment.likes.add(user)
            action = "liked"

        return Response({"detail": f"Successfully {action} comment."}, status=status.HTTP_200_OK)

    def get_object(self, comment_id):
        """Helper to fetch comment"""
        return get_object_or_404(Comment, id=comment_id)
