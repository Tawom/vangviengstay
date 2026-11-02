import pymongo
from django.conf import settings

def get_policies_collection():
    """Connect to MongoDB and return the policy_documents collection"""
    client = pymongo.MongoClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]
    return db['policy_documents']

def upsert_policy(title, content, category, embedding):
    """Save or update a policy document with its vector embedding"""
    collection = get_policies_collection()
    collection.update_one(
        {'title': title},
        {'$set': {
            'content': content,
            'category': category,
            'embedding': embedding
        }},
        upsert=True
    )

def vector_search(query_embedding, top_k=3):
    """Perform vector search using MongoDB Atlas Vector Search"""
    collection = get_policies_collection()
    
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",  # We will create this in Atlas UI
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": 10,
                "limit": top_k
            }
        },
        {
            "$project": {
                "_id": 0,
                "title": 1,
                "content": 1,
                "category": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    
    results = list(collection.aggregate(pipeline))
    
    # Convert dicts to simple objects to match our existing code structure
    class MockDoc:
        def __init__(self, data):
            self.title = data['title']
            self.content = data['content']
            self.category = data['category']
            
    return [MockDoc(res) for res in results]

def get_all_policies():
    """Read all policy documents (no embeddings needed)."""
    collection = get_policies_collection()
    docs = list(collection.find({}, {'_id': 0, 'embedding': 0}))

    class Doc:
        def __init__(self, data):
            self.title = data.get('title', '')
            self.content = data.get('content', '')
            self.category = data.get('category', 'general')

    return [Doc(d) for d in docs]