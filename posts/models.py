from django.db import models
from django.conf import settings
import re

User = settings.AUTH_USER_MODEL

# -------------------------------
# Hashtag model
# -------------------------------
class Hashtag(models.Model):
    name = models.CharField(max_length=100, unique=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.name}"


# -------------------------------
# Post model
# -------------------------------
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(blank=True)  # optional text content
    created_at = models.DateTimeField(auto_now_add=True)

    # Likes
    likes = models.ManyToManyField(User, blank=True, related_name="liked_posts")

    # Hashtags
    hashtags = models.ManyToManyField(Hashtag, blank=True, related_name="posts")

    def __str__(self):
        return f"Post {self.id} by {self.user.username}"

    def save(self, *args, **kwargs):
        # Save post first
        super().save(*args, **kwargs)

        # Extract hashtags from content
        hashtags_in_content = set(re.findall(r"#(\w+)", self.content))

        # Clear old hashtags (in case of edit)
        self.hashtags.clear()

        # Link hashtags
        for tag_name in hashtags_in_content:
            hashtag, created = Hashtag.objects.get_or_create(name=tag_name.lower())
            self.hashtags.add(hashtag)


# -------------------------------
# PostImage model
# -------------------------------
class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="post_images/")

    def __str__(self):
        return f"Image {self.id} for Post {self.post.id}"
