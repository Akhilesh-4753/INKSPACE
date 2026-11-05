from django.contrib import admin
from .models import AIGenerationLog

@admin.register(AIGenerationLog)
class AIGenerationLogAdmin(admin.ModelAdmin):
    list_display = ('prompt_summary', 'user', 'model_used', 'created_at')
    list_filter = ('model_used', 'created_at')
    search_fields = ('prompt_summary', 'user__username')
    readonly_fields = ('created_at',)
