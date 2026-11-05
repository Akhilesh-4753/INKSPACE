from django.db import models
from django.contrib.auth.models import User

# As per project requirements:
# "The chatbot does not need a separate conversation database.
# Keep conversation messages temporarily in frontend JavaScript unless persistence becomes necessary."

class AIGenerationLog(models.Model):
    """
    Optional lightweight audit log for tracking AI generation requests,
    token usage, and rate-limiting without storing raw full conversations.
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    prompt_summary = models.CharField(max_length=255)
    model_used = models.CharField(max_length=50, default='gemini-3.8-flash')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI Generation Log'
        verbose_name_plural = 'AI Generation Logs'

    def __str__(self):
        return f"AI request by {self.user or 'Guest'} at {self.created_at}"
