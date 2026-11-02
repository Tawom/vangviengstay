from django.db import models
from pgvector.django import VectorField

class PolicyDocument(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('booking', 'Booking Policy'),
        ('cancellation', 'Cancellation Policy'),
        ('payment', 'Payment Policy'),
        ('tour', 'Tour Information'),
        ('accommodation', 'Accommodation Info'),
        ('transport', 'Transport Info'),
        ('general', 'General FAQ'),
    ])
    
    # Vector field for embeddings (768 dimensions for nomic-embed-text)
    embedding = VectorField(dimensions=768, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Policy Document'
        verbose_name_plural = 'Policy Documents'
    
    def __str__(self):
        return self.title

class Conversation(models.Model):
    session_id = models.CharField(max_length=100, db_index=True)
    user_message = models.TextField()
    bot_response = models.TextField()
    relevant_docs = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.session_id} - {self.created_at}"