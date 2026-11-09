import requests
from django.conf import settings
from .mongodb_service import vector_search, get_all_policies

OLLAMA_BASE_URL = "http://127.0.0.1:11434"

# Language name mapping for the AI prompt
LANGUAGE_NAMES = {
    'en': 'English',
    'lo': 'Lao',
    'zh': 'Chinese',
    'th': 'Thai',
    'vi': 'Vietnamese',
    'fr': 'French',
}

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

def search_relevant_docs(query, top_k=3, language='en'):
    """Find most relevant policy documents using MongoDB Vector Search"""
    query_embedding = get_embedding(query)
    if not query_embedding:
        return []
    
    return vector_search(query_embedding, top_k=top_k, language=language)

def generate_response(query, relevant_docs, language='en'):
    """Generate response using DeepSeek Chat API with language awareness"""
    context = "\n\n".join([f"[{doc.title}]:\n{doc.content}" for doc in relevant_docs])
    target_language = LANGUAGE_NAMES.get(language, 'English')
    
    system_prompt = f"""You are a helpful AI assistant for Vang Vieng Stay, a booking platform in Vang Vieng, Laos.

Answer the user's question based ONLY on the provided policy documents.

IMPORTANT LANGUAGE RULES:
- You MUST respond entirely in {target_language}.
- Keep these EXACTLY as written (do NOT translate or convert):
  * Prices and currency (e.g., ₭250,000 LAK, $30 USD)
  * Email addresses (support@vangviengstay.com)
  * Phone numbers and URLs
  * Times, dates, and booking reference formats (VV-XXXX, TV-XXXX, etc.)
  * Business and operator names
- If a technical term is difficult to translate, keep it in English in parentheses.

If the provided documents do not contain enough information to answer the question, respond in {target_language}:
"I don't have specific information about that. Please contact us directly at support@vangviengstay.com for more details."
"""

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
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"Policy Documents:\n{context}\n\nQuestion: {query}"
                    }
                ],
                "temperature": 0.3,  # Lowered for more factual, consistent responses
                "max_tokens": 800    # Increased slightly for detailed answers
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"❌ DeepSeek API Error: {e}")
        return f"I'm sorry, I'm having trouble connecting right now. Please contact us directly at support@vangviengstay.com."

# Below this threshold, send every document to DeepSeek (no search needed).
# Above it, use vector search (requires local Ollama).
FULL_CONTEXT_LIMIT = 25

def get_ai_response(query, language='en'):
    """
    Small knowledge base -> send all docs (works on server, read-only).
    Large knowledge base -> vector search (requires Ollama, i.e. your Mac).
    
    Args:
        query: The user's question
        language: The target language code ('en', 'lo', etc.)
    """
    # 1. Get documents filtered by the target language
    all_docs = get_all_policies(language=language)

    if not all_docs:
        # 2. Fallback to English if target language has no docs yet (e.g., Lao not translated yet)
        if language != 'en':
            print(f"⚠️ No documents found for '{language}', falling back to English docs.")
            all_docs = get_all_policies(language='en')
        else:
            return ("I don't have any policy information loaded yet. "
                    "Please contact us directly via WhatsApp or email."), []

    # 3. Decide whether to use vector search or send all docs
    if len(all_docs) <= FULL_CONTEXT_LIMIT:
        relevant_docs = all_docs
    else:
        relevant_docs = search_relevant_docs(query, top_k=4, language=language)
        
        # 4. Fallback to English search if target language search yields nothing
        if not relevant_docs and language != 'en':
            relevant_docs = search_relevant_docs(query, top_k=4, language='en')
        
        # 5. Final safe fallback to prevent dead-ends
        if not relevant_docs:
            relevant_docs = all_docs[:4]

    # 6. Generate response (AI will still respond in target language even if context is English)
    response = generate_response(query, relevant_docs, language=language)
    return response, relevant_docs