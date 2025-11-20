from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
import string
from django.contrib.auth.hashers import make_password, check_password
import re


class CustomUser(AbstractUser):
    """
    Custom user model with:
      - Profile and social fields
      - Email verification
      - Password reset code support
      - Online / last seen tracking
    """
    email = models.EmailField(unique=True)

    # Profile fields
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    username = models.CharField(max_length=150, unique=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    banner_image = models.ImageField(upload_to="banner_images/", blank=True, null=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)

    # Followers system
    followers = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="following",
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # Email verification
    is_email_verified = models.BooleanField(default=True)

    # Password reset
    reset_password_code_hash = models.CharField(max_length=128, blank=True, null=True)
    reset_password_sent_at = models.DateTimeField(blank=True, null=True)

    # Online tracking
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    # ---------------------------------------------
    # Online / Activity methods
    # ---------------------------------------------
    def mark_online(self):
        """Mark user as online."""
        if not self.is_online:
            self.is_online = True
            self.save(update_fields=["is_online"])

    def mark_offline(self):
        """Mark user as offline and update last seen time."""
        if self.is_online:
            self.is_online = False
            self.last_seen = timezone.now()
            self.save(update_fields=["is_online", "last_seen"])

    def update_activity(self):
        """Refresh user's last activity timestamp."""
        self.last_seen = timezone.now()
        self.save(update_fields=["last_seen"])

    # ---------------------------------------------
    # Password reset methods
    # ---------------------------------------------
    def create_password_reset_code(self, code_length=6):
        """Generate and store a hashed password reset code."""
        raw_code = ''.join(random.choices(string.digits, k=code_length))
        self.reset_password_code_hash = make_password(raw_code)
        self.reset_password_sent_at = timezone.now()
        self.save(update_fields=["reset_password_code_hash", "reset_password_sent_at"])
        return raw_code

    def verify_password_reset_code(self, raw_code, expiry_minutes=15):
        """Verify the password reset code and check expiry."""
        if not self.reset_password_code_hash or not self.reset_password_sent_at:
            return False
        if timezone.now() > self.reset_password_sent_at + timedelta(minutes=expiry_minutes):
            return False
        return check_password(raw_code, self.reset_password_code_hash)

    def clear_password_reset_code(self):
        """Remove any existing reset code."""
        self.reset_password_code_hash = None
        self.reset_password_sent_at = None
        self.save(update_fields=["reset_password_code_hash", "reset_password_sent_at"])

    # ---------------------------------------------
    # Username helpers
    # ---------------------------------------------
    @staticmethod
    def _clean_username_candidate(s: str) -> str:
        """Keep only allowed chars: a-z0-9 . _ -"""
        if not s:
            return ""
        s = s.strip().lower()
        s = re.sub(r'[^a-z0-9._\-]', '', s)
        return s

    def _make_unique_username(self, base: str) -> str:
        """Generate a unique username by appending numeric suffix if needed."""
        max_len = self._meta.get_field("username").max_length or 150
        base = base[:max_len]
        candidate = base
        suffix = 0
        while True:
            qs = CustomUser.objects.filter(username=candidate)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if not qs.exists():
                return candidate
            suffix += 1
            trim_len = max_len - len(str(suffix))
            candidate = f"{base[:trim_len]}{suffix}"

    def _username_should_be_generated(self) -> bool:
        """Determine if username should be auto-generated from email."""
        uname = (self.username or "").strip()
        email = (self.email or "").strip()
        return not uname or "@" in uname or uname == email

    def save(self, *args, **kwargs):
        """Auto-generate username from email if needed."""
        email = (self.email or "").strip()
        if email and self._username_should_be_generated():
            local = email.split("@", 1)[0]
            local = self._clean_username_candidate(local)
            if not local:
                random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                local = f"user{random_part}"
            self.username = self._make_unique_username(local)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username or self.email
