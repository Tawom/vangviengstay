import requests
from django.conf import settings
from .mongodb_service import vector_search

OLLAMA_BASE_URL = "http://127.0.0.1:11434"

def get_embedding(text):
    """Get embedding from local Ollama"""
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json={"model": "nomic-embed-text", "input": text},
            timeout=10
        )
        response.raise_for_status()
        return response.json().get('embeddings', [None])[0]
    except Exception as e:
        print(f"⚠️ Ollama embedding error: {e}")
        return None

def search_relevant_docs(query, top_k=3):
    """Find most relevant policy documents using MongoDB Vector Search"""
    query_embedding = get_embedding(query)
    if not query_embedding:
        return []
    
    return vector_search(query_embedding, top_k)

def generate_response(query, relevant_docs):
    """Generate response using DeepSeek Chat API"""
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

# Below this threshold, send every document to DeepSeek (no search needed).
# Above it, use vector search (requires local Ollama).
FULL_CONTEXT_LIMIT = 25


def get_ai_response(query):
    """
    Small knowledge base -> send all docs (works on server, read-only).
    Large knowledge base -> vector search (requires Ollama, i.e. your Mac).
    """
    from .mongodb_service import get_all_policies

    all_docs = get_all_policies()

    if not all_docs:
        return ("I don't have any policy information loaded yet. "
                "Please contact us directly via WhatsApp or email."), []

    if len(all_docs) <= FULL_CONTEXT_LIMIT:
        relevant_docs = all_docs
    else:
        relevant_docs = search_relevant_docs(query, top_k=4)
        if not relevant_docs:
            relevant_docs = all_docs[:4]  # safe fallback, never dead-end

    response = generate_response(query, relevant_docs)
    return response, relevant_docs