from django.contrib import admin
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "short_content",
        "user",
        "post",
        "likes_count",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "user")
    search_fields = ("content", "user__username", "user__email", "post__id")
    readonly_fields = ("created_at", "updated_at")

    # Modern and faster than raw_id_fields — shows searchable dropdowns
    autocomplete_fields = ("user", "post")

    def short_content(self, obj):
        """Show a short preview of the comment content."""
        return (obj.content[:75] + "...") if len(obj.content) > 75 else obj.content

    short_content.short_description = "content"

    def likes_count(self, obj):
        """Show the number of likes for each comment."""
        return obj.likes.count()

    likes_count.short_description = "likes"
