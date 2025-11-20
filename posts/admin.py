from django.contrib import admin
from .models import Post, PostImage
from comments.models import Comment  # import your Comment model


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1
    readonly_fields = ["id"]
    fields = ["image"]


# Optional: show comments directly under posts
class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ["id", "created_at"]
    fields = ["user", "content", "likes", "created_at"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "content_snippet", "likes_count", "created_at"]
    list_filter = ["created_at", "user"]
    search_fields = ["user__username", "content"]
    inlines = [PostImageInline, CommentInline]  # 🔥 include both images & comments inline

    def content_snippet(self, obj):
        return obj.content[:50]

    def likes_count(self, obj):
        return obj.likes.count()


@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = ["id", "post", "image"]
    list_filter = ["post"]
