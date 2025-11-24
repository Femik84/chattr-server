from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.conf import settings
from posts.models import Post
from comments.models import Comment
from notifications.models import Notification, FCMDevice
from users.models import CustomUser
from notifications.utils import send_fcm_notification

User = settings.AUTH_USER_MODEL

# -------------------------------
# Helper function to send FCM to a user
# -------------------------------
def notify_user(user, title: str, body: str, data: dict = None):
    tokens = FCMDevice.objects.filter(user=user).values_list("token", flat=True)
    for token in tokens:
        send_fcm_notification(token, title, body, data)


# 1️⃣ When a user likes a post
@receiver(m2m_changed, sender=Post.likes.through)
def create_like_notification(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        to_user = instance.user
        for user_id in pk_set:
            from_user = instance.likes.get(pk=user_id)
            if from_user != to_user:
                Notification.objects.create(
                    from_user=from_user,
                    to_user=to_user,
                    notification_type="like",
                    post=instance,
                    message=f"{from_user.username} liked your post."
                )
                # Send push notification
                notify_user(
                    to_user,
                    title="New Like",
                    body=f"{from_user.username} liked your post",
                    data={"type": "like", "post_id": str(instance.id)}
                )


# 2️⃣ When a user comments on a post
@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created:
        from_user = instance.user
        to_user = instance.post.user
        if from_user != to_user:
            Notification.objects.create(
                from_user=from_user,
                to_user=to_user,
                notification_type="comment",
                post=instance.post,
                comment=instance,
                message=f"{from_user.username} commented: {instance.content[:30]}"
            )
            # Send push notification
            notify_user(
                to_user,
                title="New Comment",
                body=f"{from_user.username} commented: {instance.content[:30]}",
                data={"type": "comment", "post_id": str(instance.post.id)}
            )


# 3️⃣ When a user follows another user
@receiver(m2m_changed, sender=CustomUser.followers.through)
def create_follow_notification(sender, instance, action, pk_set, **kwargs):
    """
    instance → the user being followed
    pk_set → the user(s) who followed (follower IDs)
    """
    if action == "post_add":
        for follower_id in pk_set:
            from_user = CustomUser.objects.get(pk=follower_id)
            to_user = instance
            if from_user != to_user:
                Notification.objects.create(
                    from_user=from_user,
                    to_user=to_user,
                    notification_type="follow",
                    message=f"{from_user.username} started following you."
                )
                # Send push notification
                notify_user(
                    to_user,
                    title="New Follower",
                    body=f"{from_user.username} started following you",
                    data={"type": "follow"}
                )

    elif action == "post_remove":
        # Optional: delete follow notification when someone unfollows
        for follower_id in pk_set:
            Notification.objects.filter(
                from_user_id=follower_id,
                to_user=instance,
                notification_type="follow"
            ).delete()
