import json
import traceback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .services import get_ai_response

@csrf_exempt
@require_POST
def chat_api(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'anonymous')
        
        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Get AI response (this now uses MongoDB Atlas)
        bot_response, relevant_docs = get_ai_response(user_message)
        
        # Optional: Save conversation to MongoDB (commented out for now to avoid errors)
        # We can add this later if needed
        
        return JsonResponse({
            'response': bot_response,
            'sources': [doc.title for doc in relevant_docs] if relevant_docs else []
        })
    
    except Exception as e:
        print("❌ CRITICAL ERROR IN CHAT_API:")
        traceback.print_exc()
        return JsonResponse({
            'error': 'Sorry, an error occurred. Please try again.',
            'details': str(e)
        }, status=500)