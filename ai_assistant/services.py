import requests
from django.conf import settings
from django.db import connection
from django.db.models import Q
from .models import PolicyDocument

OLLAMA_BASE_URL = "http://127.0.0.1:11434"

def get_embedding(text):
    """Get embedding from local Ollama. Returns None if unavailable."""
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json={"model": "nomic-embed-text", "input": text},
            timeout=5
        )
        response.raise_for_status()
        return response.json().get('embeddings', [None])[0]
    except Exception:
        return None

def search_relevant_docs(query, top_k=3):
    """
    Smart Search: 
    - Uses Vector Search ONLY on PostgreSQL (Production)
    - Uses safe Keyword Search on SQLite (Local Mac)
    """
    try:
        # 1. Check if we are on PostgreSQL. If not, skip to fallback.
        if connection.vendor == 'postgresql':
            from pgvector.django import CosineDistance
            query_embedding = get_embedding(query)
            
            if query_embedding:
                # Evaluate immediately to a list to avoid lazy QuerySet issues
                return list(PolicyDocument.objects.annotate(
                    distance=CosineDistance('embedding', query_embedding)
                ).order_by('distance')[:top_k])
    except Exception as e:
        print(f"⚠️ Vector search skipped: {e}")

    # 2. Fallback: Safe keyword search (Works perfectly on SQLite and as a backup)
    return list(PolicyDocument.objects.filter(
        Q(title__icontains=query) | Q(content__icontains=query)
    ).distinct()[:top_k])

def generate_response(query, relevant_docs):
    """Generate response using DeepSeek Chat API"""
    # relevant_docs is now a list of objects
    context = "\n\n".join([f"{doc.title}:\n{doc.content}" for doc in relevant_docs])
    
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant for Vang Vieng Stay. Answer using ONLY the provided policy documents. If the answer is not found, say 'I don't have that specific information. Please contact us directly via WhatsApp or email.'"
                    },
                    {
                        "role": "user",
                        "content": f"Policy Documents:\n{context}\n\nQuestion: {query}"
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"❌ DeepSeek API Error: {e}")
        return "I'm sorry, I'm having trouble connecting right now. Please contact us directly."

def get_ai_response(query):
    """Main function to get AI response"""
    relevant_docs = search_relevant_docs(query)
    
    # Check if list is empty
    if not relevant_docs:
        return "I don't have information about that specific topic. Please contact us directly via WhatsApp or email.", []
    
    response = generate_response(query, relevant_docs)
    return response, relevant_docs