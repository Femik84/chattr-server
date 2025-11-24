from django.db import models
from django.conf import settings
from posts.models import Post
from comments.models import Comment

User = settings.AUTH_USER_MODEL

# -------------------------------
# Existing Notification model
# -------------------------------
class Notification(models.Model):
    class NotificationType(models.TextChoices):
        FOLLOW = "follow", "Follow"
        LIKE = "like", "Like"
        COMMENT = "comment", "Comment"

    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications_sent"
    )
    to_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications_received"
    )
    notification_type = models.CharField(
        max_length=20, choices=NotificationType.choices
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications"
    )
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications"
    )
    message = models.TextField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.notification_type})"


# -------------------------------
# New model: FCMDevice
# -------------------------------
class FCMDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fcm_devices")
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.token}"
