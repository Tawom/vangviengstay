import json
import traceback
from django.http import JsonResponse
from django.utils import translation
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
        
        # ✅ Get the current language from Django's i18n system (e.g., 'en', 'lo')
        current_language = translation.get_language() or 'en'
        
        # ✅ Pass the language to the AI response function
        bot_response, relevant_docs = get_ai_response(user_message, language=current_language)
        
        # ✅ Enhanced sources to include category and language for frontend debugging
        sources = [
            {
                'title': doc.title,
                'category': getattr(doc, 'category', 'general'),
                'language': getattr(doc, 'language', current_language)
            } 
            for doc in relevant_docs
        ] if relevant_docs else []
        
        return JsonResponse({
            'response': bot_response,
            'sources': sources
        })
    
    except Exception as e:
        print("❌ CRITICAL ERROR IN CHAT_API:")
        traceback.print_exc()
        return JsonResponse({
            'error': 'Sorry, an error occurred. Please try again.',
            'details': str(e)
        }, status=500)