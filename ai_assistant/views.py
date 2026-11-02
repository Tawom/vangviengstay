import json
import traceback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .services import get_ai_response
from .models import Conversation

@csrf_exempt
@require_POST
def chat_api(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'anonymous')
        
        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        bot_response, relevant_docs = get_ai_response(user_message)
        
        # Save conversation
        Conversation.objects.create(
            session_id=session_id,
            user_message=user_message,
            bot_response=bot_response,
            relevant_docs=[doc.id for doc in relevant_docs]
        )
        
        return JsonResponse({
            'response': bot_response,
            'sources': [doc.title for doc in relevant_docs]
        })
    
    except Exception as e:
        print("❌ CRITICAL ERROR IN CHAT_API:")
        traceback.print_exc() # This will print the EXACT line causing the error
        return JsonResponse({'error': 'An internal error occurred'}, status=500)