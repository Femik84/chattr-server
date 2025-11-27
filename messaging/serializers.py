import os
import mimetypes
from urllib.parse import urlparse

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
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "profile_picture",
            "is_online",
            "last_seen",
        ]

    def get_is_online(self, obj):
        """Consider user online if last_seen was within the last 5 minutes."""
        if not hasattr(obj, "last_seen") or obj.last_seen is None:
            return False
        return timezone.now() - obj.last_seen <= timedelta(minutes=5)

    def get_last_seen(self, obj):
        """Return ISO format of last seen timestamp, or None."""
        if not hasattr(obj, "last_seen") or obj.last_seen is None:
            return None
        return obj.last_seen.isoformat()


# ------------------------------
# Message Serializer
# ------------------------------
class MessageSerializer(serializers.ModelSerializer):
    sender = UserSummarySerializer(read_only=True)
    # computed fields
    file_url = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()
    # expose cloudinary_url (no `source=` — field name equals model attr)
    cloudinary_url = serializers.CharField(read_only=True, allow_null=True)
    # structured attachment helper for frontend
    attachment = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender",
            "text",
            "file",            # original FileField (may be null)
            "file_url",        # computed preferred URL
            "cloudinary_url",  # explicit cloudinary URL if present
            "attachment",      # structured attachment info for frontend
            "file_type",
            "is_read",
            "read_at",
            "created_at",
        ]
        read_only_fields = [
            "conversation",
            "sender",
            "is_read",
            "read_at",
            "created_at",
        ]

    def get_file_url(self, obj):
        """
        Return the attachment URL.
        Priority:
         1) cloudinary_url (used for audio/video/raw uploads)
         2) FileField URL (images uploaded via Django storage/cloudinary_storage)
        """
        # Prefer explicit cloudinary URL if present
        cloud_url = getattr(obj, "cloudinary_url", None)
        if cloud_url:
            return cloud_url

        # Otherwise try FileField
        if getattr(obj, "file", None):
            try:
                return obj.file.url
            except Exception:
                return None

        return None

    def _infer_type_from_extension(self, ext: str):
        """Helper to map file extensions to high-level types."""
        if not ext:
            return None
        ext = ext.lower()
        image_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}
        audio_exts = {".m4a", ".mp3", ".wav", ".ogg", ".aac", ".flac", ".webm"}
        video_exts = {".mp4", ".mov", ".avi", ".webm", ".mkv"}
        document_exts = {
            ".pdf",
            ".doc",
            ".docx",
            ".txt",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
        }

        if ext in image_exts:
            return "image"
        if ext in audio_exts:
            return "audio"
        if ext in video_exts:
            return "video"
        if ext in document_exts:
            return "document"
        # fallback
        return "file"

    def _infer_type_from_mime(self, mime: str):
        """Map MIME types to high-level types."""
        if not mime:
            return None
        if mime.startswith("image/"):
            return "image"
        if mime.startswith("audio/"):
            return "audio"
        if mime.startswith("video/"):
            return "video"
        if mime in ("application/pdf", "text/plain", "application/msword") or mime.startswith("application/"):
            return "document"
        return "file"

    def get_file_type(self, obj):
        """
        Determine file type from the model field, cloudinary_url, or file extension.
        Priority:
         1) model.field file_type (explicitly set when saving the message)
         2) infer from cloudinary_url (extension or MIME)
         3) infer from FileField.name extension
         4) fallback to "file"
        """
        # 1) If stored explicitly, use it
        stored = getattr(obj, "file_type", None)
        if stored:
            return stored

        # 2) Try to infer from cloudinary_url if present
        cloud_url = getattr(obj, "cloudinary_url", None)
        if cloud_url:
            try:
                parsed = urlparse(cloud_url)
                path = parsed.path or ""
                _, ext = os.path.splitext(path)
                if ext:
                    inferred = self._infer_type_from_extension(ext)
                    if inferred:
                        return inferred
                # If no extension, try MIME guess
                mime, _ = mimetypes.guess_type(cloud_url)
                inferred = self._infer_type_from_mime(mime)
                if inferred:
                    return inferred
            except Exception:
                pass

        # 3) Try to infer from the FileField name (if present)
        if getattr(obj, "file", None) and getattr(obj.file, "name", None):
            try:
                file_name = obj.file.name.lower()
                _, ext = os.path.splitext(file_name)
                inferred = self._infer_type_from_extension(ext)
                if inferred:
                    return inferred
            except Exception:
                pass

        # 4) As a last resort, return "file" so frontend has a deterministic value
        return "file"

    def get_attachment(self, obj):
        """
        Return a small structured object that frontend can use directly:
        {
            "url": ...,
            "type": "audio"|"image"|"video"|"document"|"file",
            "source": "cloudinary"|"file",
            "name": "<filename if available>"
        }
        This prevents frontend bugs where it only checks message.file and misses cloudinary_url.
        """
        url = self.get_file_url(obj)
        if not url:
            return None

        source = "cloudinary" if getattr(obj, "cloudinary_url", None) else "file"
        # try to obtain a filename
        file_name = None
        # If FileField exists, prefer its name
        if getattr(obj, "file", None) and getattr(obj.file, "name", None):
            file_name = os.path.basename(obj.file.name)
        else:
            # attempt to parse the path portion of the URL
            try:
                parsed = urlparse(url)
                file_name = os.path.basename(parsed.path) or None
            except Exception:
                file_name = None

        return {
            "url": url,
            "type": self.get_file_type(obj),
            "source": source,
            "name": file_name,
        }

    def create(self, validated_data):
        """
        Create a new message, link to conversation, and update conversation's last_message.
        (Same behaviour as before — keep business logic in the view/consumer)
        """
        request = self.context.get("request")
        conversation = self.context.get("conversation")

        if not conversation:
            raise serializers.ValidationError("Conversation context is required.")

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            **validated_data,
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
        """Count of unread messages received by the current user."""
        request = self.context.get("request")
        if not request or not request.user:
            return 0
        return (
            Message.objects.filter(conversation=obj, is_read=False)
            .exclude(sender=request.user)
            .count()
        )

    def get_unread_sent_count(self, obj):
        """Count of unread messages sent by the current user."""
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