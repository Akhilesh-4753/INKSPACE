from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.core.exceptions import ValidationError

class Profile(models.Model):
    """
    User Profile extending Django's built-in User model with avatar, bio, and role.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True, default='Passionate writer and lifelong learner.')
    role = models.CharField(max_length=100, blank=True, default='Blogger · Developer')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def get_avatar_url(self):
        """
        Return the proper URL for the user avatar.
        Supports both local uploaded files in /media/ and external URLs,
        or None if no avatar is set.
        """
        if not self.avatar:
            return None
        val = str(self.avatar).strip()
        if val.startswith("http://") or val.startswith("https://"):
            return val
        try:
            return self.avatar.url
        except Exception:
            return None

class Follow(models.Model):
    """
    Follow relationship between users.
    Enforces uniqueness and prevents self-following at the model and database constraint levels.
    """
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_set')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers_set')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['follower', 'following'], name='unique_user_follow'),
            models.CheckConstraint(condition=~models.Q(follower=models.F('following')), name='prevent_self_follow'),
        ]
        verbose_name = 'Follow Relationship'
        verbose_name_plural = 'Follow Relationships'

    def clean(self):
        if self.follower_id and self.following_id and self.follower_id == self.following_id:
            raise ValidationError("A blog author cannot follow themselves.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Automatically create or save profile when User is created/saved."""
    if created:
        Profile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()

