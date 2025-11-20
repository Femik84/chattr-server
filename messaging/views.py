from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from django.db import models
from django.utils import timezone

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    ConversationCreateSerializer,
    MessageSerializer,
)


class StandardResultsSetPagination(PageNumberPagination):
    """Pagination for messages (load more style)."""
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ConversationListView(generics.ListCreateAPIView):
    """List user's conversations or create a new one."""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(
            models.Q(user1=user) | models.Q(user2=user)
        ).select_related(
            'user1', 'user2', 'last_message', 'last_message__sender'
        ).prefetch_related(
            'messages'  # For calculating unread counts
        ).order_by("-updated_at")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ConversationCreateSerializer
        return ConversationSerializer

    def get_serializer_context(self):
        """Pass request to serializer context."""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class ConversationStartView(APIView):
    """Explicit endpoint to start or get an existing conversation."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ConversationCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()  # Uses get_or_create_1on1 internally

        response_serializer = ConversationSerializer(
            conversation, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ConversationDetailView(generics.RetrieveAPIView):
    """Get details of a single conversation (participants, last message)."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ConversationSerializer
    
    def get_queryset(self):
        return Conversation.objects.select_related(
            'user1', 'user2', 'last_message', 'last_message__sender'
        ).prefetch_related('messages')

    def get_object(self):
        conversation = super().get_object()
        user = self.request.user
        if user not in [conversation.user1, conversation.user2]:
            raise PermissionDenied("You are not a participant in this conversation.")
        return conversation


class MessageListCreateView(generics.ListCreateAPIView):
    """List or send messages in a conversation."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageSerializer
    pagination_class = StandardResultsSetPagination

    def get_conversation(self):
        """Get conversation object and check permissions."""
        conversation_id = self.kwargs["conversation_id"]
        conversation = Conversation.objects.select_related(
            'user1', 'user2'
        ).get(pk=conversation_id)
        user = self.request.user
        if user not in [conversation.user1, conversation.user2]:
            raise PermissionDenied("You are not a participant in this conversation.")
        return conversation

    def get_queryset(self):
        conversation = self.get_conversation()
        return Message.objects.filter(
            conversation=conversation
        ).select_related('sender').order_by("-created_at")

    def get_serializer_context(self):
        """Pass conversation and request to serializer context."""
        context = super().get_serializer_context()
        context["conversation"] = self.get_conversation()
        return context

    def perform_create(self, serializer):
        """Save message using serializer with proper context."""
        serializer.save()


class MarkMessagesReadView(APIView):
    """Mark all unread messages in a conversation as read."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, conversation_id):
        """Mark all messages in a conversation as read by the recipient."""
        try:
            conversation = Conversation.objects.get(pk=conversation_id)
        except Conversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user

        if user not in [conversation.user1, conversation.user2]:
            raise PermissionDenied("You are not a participant in this conversation.")

        # Only mark messages as read that:
        # 1. Are in this conversation
        # 2. Were NOT sent by the current user (received messages)
        # 3. Are currently unread
        updated = Message.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(sender=user).update(
            is_read=True, 
            read_at=timezone.now()
        )

        return Response(
            {
                "marked_read": updated,
                "conversation_id": conversation_id
            }, 
            status=status.HTTP_200_OK
        )