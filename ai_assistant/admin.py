from django.contrib import admin
from .models import PolicyDocument, Conversation

@admin.register(PolicyDocument)
class PolicyDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'updated_at']
    list_filter = ['category']
    search_fields = ['title', 'content']

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'created_at']
    list_filter = ['created_at']
    readonly_fields = ['session_id', 'user_message', 'bot_response', 'relevant_docs', 'created_at']