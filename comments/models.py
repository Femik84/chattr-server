from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Comment(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        related_name="comments"
    )
    content = models.TextField()
    likes = models.ManyToManyField(
        User,
        blank=True,
        related_name="liked_comments"
    )
    # New field for nested comments (replies)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        help_text="If set, this comment is a reply to another comment"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["post", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        user_str = getattr(self.user, "username", str(self.user))
        if self.parent:
            return f"Reply {self.id} by {user_str} to Comment {self.parent_id}"
        return f"Comment {self.id} by {user_str} on Post {self.post_id}"
