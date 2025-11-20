from django.conf import settings
from django.db import models
from django.db.models import Q, F
from django.utils import timezone


class ConversationManager(models.Manager):
    def get_or_create_1on1(self, user_a, user_b):
        """Return an existing 1-on-1 conversation between two users or create it.

        This method enforces an ordering so (user1, user2) uniqueness is stable.
        """
        if user_a.id == user_b.id:
            raise ValueError("Cannot create a conversation with the same user as both participants")

        # enforce stable ordering to make unique constraint simple
        if user_a.id < user_b.id:
            user1, user2 = user_a, user_b
        else:
            user1, user2 = user_b, user_a

        conversation = self.filter(user1=user1, user2=user2).first()
        if conversation:
            return conversation, False

        conversation = self.create(user1=user1, user2=user2)
        return conversation, True


class Conversation(models.Model):
    """A 1-on-1 conversation between exactly two users.

    We store user1 and user2 in a canonical order (user1.id < user2.id) to
    ensure a unique pair per conversation.
    """

    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="conversations_as_user1",
        on_delete=models.CASCADE,
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="conversations_as_user2",
        on_delete=models.CASCADE,
    )

    # optional: cache of the most recent message for fast chat-list queries
    last_message = models.ForeignKey(
        "Message",
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ConversationManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user1", "user2"], name="unique_1on1_conversation"),
            models.CheckConstraint(check=~Q(user1=F("user2")), name="no_self_conversation"),

        ]
        indexes = [models.Index(fields=["updated_at"])]

    def save(self, *args, **kwargs):
        # ensure canonical ordering before saving
        if self.user1_id and self.user2_id and self.user1_id > self.user2_id:
            self.user1, self.user2 = self.user2, self.user1
        super().save(*args, **kwargs)

    def other_user(self, user):
        """Return the other participant for a given user instance."""
        if user == self.user1:
            return self.user2
        if user == self.user2:
            return self.user1
        raise ValueError("User is not a participant in this conversation")

    def __str__(self):
        return f"Conversation({self.user1} <-> {self.user2})"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, related_name="messages", on_delete=models.CASCADE
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="sent_messages", on_delete=models.CASCADE
    )

    text = models.TextField(blank=True)
    file = models.FileField(upload_to="attachments/%Y/%m/%d/", null=True, blank=True)

    # read receipt for the recipient (since 1-on-1, a single flag is sufficient)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["conversation", "created_at"])]

    def mark_as_read(self, when=None):
        if not self.is_read:
            self.is_read = True
            self.read_at = when or timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # update conversation.last_message and touch updated_at on new messages
        if is_new:
            Conversation.objects.filter(pk=self.conversation_id).update(last_message_id=self.pk, updated_at=timezone.now())

    def __str__(self):
        preview = (self.text[:50] + "...") if self.text and len(self.text) > 50 else (self.text or "<attachment>")
        return f"Message({self.sender}, {preview})"


