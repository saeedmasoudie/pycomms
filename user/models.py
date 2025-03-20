import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django_countries.fields import CountryField


# Create your models here.

class CustomUser(AbstractUser):
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    profile_cover = models.ImageField(upload_to="profile_covers/", blank=True, null=True)
    is_muted = models.BooleanField(default=False)
    is_deafened = models.BooleanField(default=False)
    reset_key = models.UUIDField(default=uuid.uuid4, editable=False, blank=True, null=True)
    date_key = models.DateTimeField(blank=True, null=True)
    country = CountryField(null=True, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.username


class Conversation(models.Model):
    """Model to track conversations between users."""
    participants = models.ManyToManyField(CustomUser, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation {self.id} ({', '.join(user.username for user in self.participants.all())})"

class DirectMessage(models.Model):
    """Model for direct messages between users."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="sent_messages")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"

class VoiceActivity(models.Model):
    """Tracks voice chat activities like mute/deafen."""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="voice_activity")
    is_muted = models.BooleanField(default=False)
    is_deafened = models.BooleanField(default=False)
    volume_level = models.IntegerField(default=100)  # 0 to 100

    def __str__(self):
        return f"{self.user.username} Voice Settings"

class UserStatus(models.Model):
    """Tracks if a user is online/offline and their last seen."""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="status")
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now_add=True)
    status_message = models.CharField(max_length=100, default="Hey there! I'm using PyComms.")

    def __str__(self):
        return f"{self.user.username} - {'Online' if self.is_online else 'Offline'}"
