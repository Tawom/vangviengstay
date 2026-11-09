import pymongo
from django.conf import settings


def get_policies_collection():
    """Connect to MongoDB and return the policy_documents collection"""
    client = pymongo.MongoClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]
    return db['policy_documents']


def upsert_policy(title, content, category, embedding, language='en'):
    """
    Save or update a policy document with its vector embedding.
    
    Args:
        title: Document title
        content: Document content
        category: Document category
        embedding: 768-dimensional vector embedding
        language: Language code ('en', 'lo', 'zh', etc.)
    """
    collection = get_policies_collection()
    
    # ✅ Use title + language as unique identifier
    collection.update_one(
        {'title': title, 'language': language},
        {'$set': {
            'title': title,  # ✅ Ensure title is stored
            'content': content,
            'category': category,
            'language': language,
            'embedding': embedding
        }},
        upsert=True
    )


def vector_search(query_embedding, top_k=3, language='en'):
    """
    Perform vector search using MongoDB Atlas Vector Search.
    
    Args:
        query_embedding: Query vector (768 dimensions)
        top_k: Number of results to return
        language: Filter results by language code
    
    Returns:
        List of MockDoc objects with title, content, category, language
    """
    collection = get_policies_collection()
    
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": 50,  # ✅ Increased for better filtering results
                "limit": top_k,
                "filter": {
                    "language": {"$eq": language}  # ✅ Filter by language
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "title": 1,
                "content": 1,
                "category": 1,
                "language": 1,  # ✅ Include language in results
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    
    results = list(collection.aggregate(pipeline))
    
    # ✅ If no results in target language, fallback to English
    if not results and language != 'en':
        print(f"⚠️  No '{language}' docs found, falling back to English")
        pipeline[0]["$vectorSearch"]["filter"] = {"language": {"$eq": "en"}}
        results = list(collection.aggregate(pipeline))
    
    # Convert dicts to simple objects to match our existing code structure
    class MockDoc:
        def __init__(self, data):
            self.title = data.get('title', '')
            self.content = data.get('content', '')
            self.category = data.get('category', 'general')
            self.language = data.get('language', 'en')  # ✅ Added
            self.score = data.get('score', 0)           # ✅ Added for debugging
            
    return [MockDoc(res) for res in results]


def get_all_policies(language=None):
    """
    Read all policy documents (no embeddings needed).
    
    Args:
        language: Optional language filter. If None, returns all languages.
    """
    collection = get_policies_collection()
    
    # ✅ Build query filter
    query_filter = {}
    if language:
        query_filter['language'] = language
    
    docs = list(collection.find(query_filter, {'_id': 0, 'embedding': 0}))

    class Doc:
        def __init__(self, data):
            self.title = data.get('title', '')
            self.content = data.get('content', '')
            self.category = data.get('category', 'general')
            self.language = data.get('language', 'en')  # ✅ Added

    return [Doc(d) for d in docs]


def clear_language(language):
    """
    Delete all documents for a specific language.
    Useful before re-importing updated translations.
    """
    collection = get_policies_collection()
    result = collection.delete_many({'language': language})
    return result.deleted_count


def clear_all():
    """Delete all documents in the collection. USE WITH CAUTION."""
    collection = get_policies_collection()
    result = collection.delete_many({})
    return result.deleted_count