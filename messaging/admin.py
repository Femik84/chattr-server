from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "user1", "user2", "last_message_preview", "updated_at", "created_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("user1__username", "user2__username")
    ordering = ("-updated_at",)

    def last_message_preview(self, obj):
        if obj.last_message and obj.last_message.text:
            return obj.last_message.text[:40]
        elif obj.last_message:
            return "<attachment>"
        return "-"
    last_message_preview.short_description = "Last Message"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "short_text", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("sender__username", "conversation__user1__username", "conversation__user2__username", "text")
    ordering = ("-created_at",)

    def short_text(self, obj):
        return obj.text[:50] if obj.text else "<attachment>"
    short_text.short_description = "Message"
