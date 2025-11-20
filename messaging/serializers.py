from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Conversation, Message
from datetime import timedelta

User = get_user_model()


# ------------------------------
# User Serializer with online status
# ------------------------------
class UserSummarySerializer(serializers.ModelSerializer):
    """Lightweight user serializer including online status and last seen."""
    is_online = serializers.SerializerMethodField()
    last_seen = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "profile_picture", "is_online", "last_seen"]

    def get_is_online(self, obj):
        """Consider user online if last_seen was within the last 5 minutes."""
        if not hasattr(obj, 'last_seen') or obj.last_seen is None:
            return False
        return timezone.now() - obj.last_seen <= timedelta(minutes=5)

    def get_last_seen(self, obj):
        """Return ISO format of last seen timestamp, or None."""
        if not hasattr(obj, 'last_seen') or obj.last_seen is None:
            return None
        return obj.last_seen.isoformat()


# ------------------------------
# Message Serializer
# ------------------------------
class MessageSerializer(serializers.ModelSerializer):
    sender = UserSummarySerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender",
            "text",
            "file",
            "file_url",
            "file_type",
            "is_read",
            "read_at",
            "created_at",
        ]
        read_only_fields = ["conversation", "sender", "is_read", "read_at", "created_at"]

    def get_file_url(self, obj):
        """Return full URL for file if it exists."""
        if obj.file:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None

    def get_file_type(self, obj):
        """Determine file type based on extension."""
        if not obj.file:
            return None
        
        file_name = obj.file.name.lower()
        if any(file_name.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
            return "image"
        if any(file_name.endswith(ext) for ext in ['.m4a', '.mp3', '.wav', '.ogg', '.aac', '.flac']):
            return "audio"
        return "file"

    def create(self, validated_data):
        """Create a new message, link to conversation, and update conversation's last_message."""
        request = self.context.get("request")
        conversation = self.context.get("conversation")

        if not conversation:
            raise serializers.ValidationError("Conversation context is required.")

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            **validated_data
        )

        # Update conversation last message
        conversation.last_message = message
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=["last_message", "updated_at"])

        return message


# ------------------------------
# Conversation Serializer
# ------------------------------
class ConversationSerializer(serializers.ModelSerializer):
    user1 = UserSummarySerializer(read_only=True)
    user2 = UserSummarySerializer(read_only=True)
    last_message = MessageSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()
    unread_sent_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "user1",
            "user2",
            "last_message",
            "unread_count",
            "unread_sent_count",
            "created_at",
            "updated_at",
        ]

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if not request or not request.user:
            return 0
        return Message.objects.filter(conversation=obj, is_read=False).exclude(sender=request.user).count()

    def get_unread_sent_count(self, obj):
        request = self.context.get("request")
        if not request or not request.user:
            return 0
        return Message.objects.filter(conversation=obj, sender=request.user, is_read=False).count()


# ------------------------------
# Conversation Creation Serializer
# ------------------------------
class ConversationCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

    def validate_user_id(self, value):
        request_user = self.context["request"].user
        if request_user.id == value:
            raise serializers.ValidationError("Cannot start a conversation with yourself.")
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User not found.")
        return value

    def create(self, validated_data):
        request_user = self.context["request"].user
        other_user = User.objects.get(id=validated_data["user_id"])
        conversation, _ = Conversation.objects.get_or_create_1on1(request_user, other_user)
        return conversation
