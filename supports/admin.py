from django.contrib import admin
from .models import Conversation, Message, AgentLog

# Register your models here.


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "order", "created_at", "manager_involve", "risk_assessed")
    list_filter = ("created_at",)
    search_fields = ("user__username", "order__id")

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "role", "content", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("conversation__id", "content")

@admin.register(AgentLog)
class AgentLogAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "event_type", "message", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("conversation__id", "message")