import json
import base64
import uuid
import io
import cloudinary.uploader

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

            # Debug logging
            print(f"✅ Message saved: ID={message.id}, has_file={bool(message.file) or bool(message.cloudinary_url)}")
            if getattr(message, "file", None):
                try:
                    print(f"✅ File URL: {message.file.url}")
                except Exception:
                    pass
            if getattr(message, "cloudinary_url", None):
                print(f"✅ Cloudinary URL: {message.cloudinary_url}")
            print(f"✅ File type: {message.file_type}")

            # Serialize full REST-style response
            serialized = await self.serialize_message(message)
            print(f"✅ Serialized data: {serialized}")

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
            import traceback
            traceback.print_exc()
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
        """
        Save message to database.
        - Fixes base64 decoding bug.
        - Infers file_type from extension if not provided.
        - Uploads audio/video with resource_type='video' and documents with resource_type='raw'.
        - Keeps image uploads via Django FileField (cloudinary_storage handles them as images).
        """
        conversation = Conversation.objects.get(id=self.conversation_id)

        # Decode file if provided
        decoded_file = None
        file_obj = None
        if file_base64 and file_name:
            try:
                # Handle data URI format: "data:<mime>;base64,<data>"
                if file_base64.startswith("data:"):
                    header, encoded = file_base64.split(",", 1)
                    decoded_file = base64.b64decode(encoded)
                else:
                    # Plain base64 string
                    decoded_file = base64.b64decode(file_base64)

                # Generate unique filename for storage if needed
                unique_name = f"{uuid.uuid4().hex}_{file_name}"
                file_obj = ContentFile(decoded_file, name=unique_name)

                print(f"📎 File decoded: {unique_name}, size: {len(decoded_file)} bytes")
            except Exception as e:
                print(f"❌ Error decoding base64 file: {e}")
                raise ValueError(f"Invalid file data: {str(e)}")

        # Create message without file first
        msg = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            text=text or "",
            file_type=file_type,  # may be updated below
        )

        print(f"💾 Message created with ID: {msg.id}")

        # If there's a decoded file, handle upload according to type
        if decoded_file:
            # Infer file_type from extension when not provided
            inferred_type = file_type
            if not inferred_type and file_name:
                lower = file_name.lower()
                if any(lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']):
                    inferred_type = "image"
                elif any(lower.endswith(ext) for ext in ['.mp3', '.m4a', '.wav', '.ogg', '.aac', '.flac']):
                    inferred_type = "audio"
                elif any(lower.endswith(ext) for ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']):
                    inferred_type = "video"
                elif any(lower.endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.ppt', '.pptx']):
                    inferred_type = "document"
                else:
                    inferred_type = "file"

            msg.file_type = inferred_type

            try:
                # AUDIO/VIDEO: upload with resource_type='video' (Cloudinary treats audio under video)
                if inferred_type in ("audio", "video"):
                    # Upload bytes directly to Cloudinary as video resource
                    upload_bytes = io.BytesIO(decoded_file)
                    result = cloudinary.uploader.upload(
                        upload_bytes,
                        resource_type="video",
                        public_id=f"attachments/{uuid.uuid4().hex}_{file_name}",
                        overwrite=True,
                    )
                    msg.cloudinary_url = result.get("secure_url") or result.get("url")
                    # We intentionally do NOT set msg.file (avoid default image upload path)
                    msg.save(update_fields=["file_type", "cloudinary_url"])
                    print(f"☁️ Uploaded audio/video to Cloudinary: {msg.cloudinary_url}")

                # IMAGE: use Django FileField so existing storage (cloudinary_storage) handles it as image
                elif inferred_type == "image":
                    msg.file = file_obj
                    # msg.save() will trigger storage to upload via cloudinary_storage as image
                    msg.save()
                    print(f"☁️ Image saved via FileField storage, URL (may be available after refresh): {getattr(msg.file, 'url', None)}")

                # DOCUMENTS / OTHER: upload as raw so Cloudinary won't try to validate as image
                else:
                    upload_bytes = io.BytesIO(decoded_file)
                    result = cloudinary.uploader.upload(
                        upload_bytes,
                        resource_type="raw",
                        public_id=f"attachments/{uuid.uuid4().hex}_{file_name}",
                        overwrite=True,
                    )
                    msg.cloudinary_url = result.get("secure_url") or result.get("url")
                    msg.save(update_fields=["file_type", "cloudinary_url"])
                    print(f"☁️ Uploaded raw file to Cloudinary: {msg.cloudinary_url}")

            except cloudinary.exceptions.Error as e:
                # Log and raise a clear error so the caller can handle it
                print(f"❌ Cloudinary upload error: {e}")
                raise ValueError(f"Cloudinary upload failed: {str(e)}")

        else:
            # No file to attach — ensure file_type is saved if provided earlier
            if file_type:
                msg.file_type = file_type
                msg.save(update_fields=["file_type"])

        # Refresh from DB to get any fields filled by storage signals
        msg.refresh_from_db()

        # Try to print final URL(s) if available
        if getattr(msg, "cloudinary_url", None):
            print(f"🔗 Final cloudinary_url: {msg.cloudinary_url}")
        if getattr(msg, "file", None):
            try:
                print(f"🔗 Final file URL: {msg.file.url}")
            except Exception:
                pass

        return msg

    @database_sync_to_async
    def serialize_message(self, message):
        """
        Serialize message for WebSocket transmission.
        Cloudinary URLs are already absolute, so just use them directly.
        """
        serializer = MessageSerializer(message)
        data = serializer.data

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