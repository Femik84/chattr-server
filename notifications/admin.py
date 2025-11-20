from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "from_user",
        "to_user",
        "notification_type",
        "post",
        "comment",
        "is_read",
        "created_at",
    )
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = (
        "from_user__username",
        "to_user__username",
        "message",
    )
    ordering = ("-created_at",)
