from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
import string
from django.contrib.auth.hashers import make_password, check_password


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    # Profile fields
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    username = models.CharField(max_length=150, unique=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    banner_image = models.ImageField(upload_to="banner_images/", blank=True, null=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)

    # Followers system (users can follow other users)
    followers = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="following",
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # Email verification status
    is_email_verified = models.BooleanField(default=True)  # now auto-verified at signup

    # Password reset
    reset_password_code_hash = models.CharField(max_length=128, blank=True, null=True)
    reset_password_sent_at = models.DateTimeField(blank=True, null=True)

    # ---------------------------------------------
    # Password reset methods
    # ---------------------------------------------
    def create_password_reset_code(self, code_length=6):
        raw_code = ''.join(random.choices(string.digits, k=code_length))
        self.reset_password_code_hash = make_password(raw_code)
        self.reset_password_sent_at = timezone.now()
        self.save(update_fields=["reset_password_code_hash", "reset_password_sent_at"])
        return raw_code

    def verify_password_reset_code(self, raw_code, expiry_minutes=15):
        if not self.reset_password_code_hash or not self.reset_password_sent_at:
            return False
        if timezone.now() > self.reset_password_sent_at + timedelta(minutes=expiry_minutes):
            return False
        return check_password(raw_code, self.reset_password_code_hash)

    def clear_password_reset_code(self):
        self.reset_password_code_hash = None
        self.reset_password_sent_at = None
        self.save(update_fields=["reset_password_code_hash", "reset_password_sent_at"])

    def __str__(self):
        return self.username or self.email
