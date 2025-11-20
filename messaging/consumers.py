import json
import base64
import uuid

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.files.base import ContentFile
from django.utils import timezone

from messaging.models import Conversation, Message
from messaging.serializers import MessageSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"
        self.user = self.scope.get("user")

        # Must be logged in
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        # Must belong to conversation
        is_member = await self.is_user_in_conversation()
        if not is_member:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Auto-mark messages as read when user opens chat
        await self.mark_messages_as_read()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(json.dumps({
                "error": "Invalid JSON format"
            }))
            return

        event_type = data.get("type", "message")

        # ==========================
        # READ RECEIPTS
        # ==========================
        if event_type == "mark_read":
            await self.mark_messages_as_read()
            # Broadcast read receipt to other user
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "read_receipt",
                    "user_id": self.user.id,
                },
            )
            return

        # ==========================
        # TYPING INDICATOR
        # ==========================
        if event_type == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "user_id": self.user.id,
                },
            )
            return

        # ==========================
        # MESSAGE SEND
        # ==========================
        text = data.get("text", "")
        file_base64 = data.get("file_base64")
        file_name = data.get("file_name")
        file_type = data.get("file_type")

        # Validate message
        if not text and not file_base64:
            await self.send(json.dumps({
                "error": "Message must contain text or file"
            }))
            return

        try:
            # Save message to DB
            message = await self.save_message(
                text=text,
                file_base64=file_base64,
                file_name=file_name,
                file_type=file_type,
            )

            # Serialize full REST-style response
            serialized = await self.serialize_message(message)

            # Broadcast to all users in the conversation
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": serialized,
                },
            )
        except Exception as e:
            print(f"❌ Error saving message: {e}")
            await self.send(json.dumps({
                "error": f"Failed to save message: {str(e)}"
            }))

    async def chat_message(self, event):
        """Send full message object to WebSocket."""
        await self.send(json.dumps(event["message"]))

    async def typing_indicator(self, event):
        """Send typing event to UI (only to other users)."""
        # Don't send typing indicator back to the sender
        if event["user_id"] != self.user.id:
            await self.send(json.dumps({
                "type": "typing",
                "user_id": event["user_id"]
            }))

    async def read_receipt(self, event):
        """Send read receipt to UI."""
        # Only send to the message sender
        if event["user_id"] != self.user.id:
            await self.send(json.dumps({
                "type": "read_receipt",
                "user_id": event["user_id"]
            }))

    # ============================================================
    # DATABASE HELPERS
    # ============================================================

    @database_sync_to_async
    def is_user_in_conversation(self):
        try:
            c = Conversation.objects.get(id=self.conversation_id)
            return self.user == c.user1 or self.user == c.user2
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, text=None, file_base64=None, file_name=None, file_type=None):
        conversation = Conversation.objects.get(id=self.conversation_id)

        file_obj = None
        if file_base64 and file_name:
            try:
                # Handle data URI format: "data:image/jpeg;base64,..."
                if file_base64.startswith("data:"):
                    # Split the data URI
                    header, encoded = file_base64.split(",", 1)
                    decoded_file = base64.b64decode(encoded)
                else:
                    # Plain base64 string
                    decoded_file = base64.b64decode(file_base64)

                # Generate unique filename
                unique_name = f"{uuid.uuid4().hex}_{file_name}"
                file_obj = ContentFile(decoded_file, name=unique_name)
            except Exception as e:
                print(f"❌ Error decoding base64 file: {e}")
                raise ValueError(f"Invalid file data: {str(e)}")

        # Create message
        msg = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            text=text or "",
            file=file_obj,
        )

        # Set file_type if file was uploaded
        if file_obj and file_type:
            msg.file_type = file_type
            msg.save()

        return msg

    @database_sync_to_async
    def serialize_message(self, message):
        serializer = MessageSerializer(message)
        data = serializer.data
        
        # Convert relative file URLs to absolute URLs
        if data.get("file"):
            file_url = data["file"]
            # If it's a relative path, make it absolute
            if not file_url.startswith("http"):
                from django.conf import settings
                # Get the base URL from settings or construct it
                base_url = getattr(settings, 'BASE_URL', f'http://{settings.ALLOWED_HOSTS[0]}:8000')
                data["file"] = f"{base_url}{file_url}"
        
        # Ensure file_url field is set (some serializers might use different field names)
        if not data.get("file_url") and data.get("file"):
            data["file_url"] = data["file"]
        
        return data

    @database_sync_to_async
    def mark_messages_as_read(self):
        """Mark unread messages (from the other user) as read."""
        conversation = Conversation.objects.get(id=self.conversation_id)
        qs = Message.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(sender=self.user)

        now = timezone.now()
        count = qs.update(is_read=True, read_at=now)
        
        return count