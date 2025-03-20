from django.db import models

from user.models import CustomUser


# Create your models here.
class Channel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    password = models.CharField(max_length=255, blank=True, null=True)  # Optional password
    banned_users = models.ManyToManyField(CustomUser, related_name="banned_channels", blank=True)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="owned_channels")

    def is_user_banned(self, user):
        """Check if a user is banned from this channel."""
        return self.banned_users.filter(id=user.id).exists()

    def is_password_protected(self):
        return bool(self.password)

    def check_password(self, password):
        if self.password is not None:
            if self.password == password:
                return True
        return False


    def __str__(self):
        return self.name

class ChannelMessage(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.sender.username} in {self.channel.name} at {self.timestamp}"


class ChannelMember(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=False)
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("moderator", "Moderator"),
        ("member", "Member"),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="member")

class BannedMember(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="banned_members")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    banned_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True)