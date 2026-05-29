from django.contrib import admin

from .models import AppEvent, Conversation, Message


@admin.register(AppEvent)
class AppEventAdmin(admin.ModelAdmin):
    list_display = ("id", "event_type", "event_time")
    list_filter = ("event_type",)
    search_fields = ("event_type",)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "created_at", "message_count")
    list_filter = ("created_at", "is_active")
    search_fields = ("title", "user__username")
    readonly_fields = ("created_at", "updated_at")

    def message_count(self, obj):
        return obj.messages.count()

    message_count.short_description = "Messages"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "role", "created_at", "tokens_used")
    list_filter = ("role", "created_at", "conversation")
    search_fields = ("content", "conversation__title")
    readonly_fields = ("created_at", "content_preview")

    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    content_preview.short_description = "Content Preview"
