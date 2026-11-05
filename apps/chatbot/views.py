import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render
from .services import GeminiService
from .models import AIGenerationLog

gemini_service = GeminiService()

@require_POST
def generate_blog_api(request):
    """
    POST endpoint: Generates complete title, description, and structured article
    content from a given topic and category.
    
    Expected JSON payload:
    {
        "topic": "Benefits of learning Python",
        "category": "Technology"
    }

    Returns:
    {
        "success": true,
        "data": {
            "title": "Why Learning Python Is a Great Investment in Your Future",
            "description": "Discover why Python is one of the most useful...",
            "content": "<h3>Introduction</h3>...",
            "suggested_tags": ["Python", "Coding", "Career"]
        }
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON format in request.'}, status=400)

    topic = data.get('topic', '').strip()
    category = data.get('category', 'Technology').strip()

    if not topic:
        return JsonResponse({'success': False, 'error': 'Please provide a topic for your blog post.'}, status=400)

    if len(topic) > 300:
        return JsonResponse({'success': False, 'error': 'Topic is too long (maximum 300 characters).'}, status=400)

    try:
        result = gemini_service.generate_blog_package(topic=topic, category=category)

        # Audit log
        user = request.user if request.user.is_authenticated else None
        AIGenerationLog.objects.create(
            user=user,
            prompt_summary=topic[:250],
            model_used=result.get('model_used', 'gemini-3.8-flash')
        )

        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f"AI generation failed: {str(e)}"
        }, status=500)

@require_POST
def chat_message_api(request):
    """
    POST endpoint: Conversational AI writing assistant communication.
    Accepts user prompts, drafting inquiries, or headline generation requests.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON in request.'}, status=400)

    message = data.get('message', '').strip()
    context = data.get('context', {})

    if not message:
        return JsonResponse({'success': False, 'error': 'Message cannot be empty.'}, status=400)

    try:
        reply = gemini_service.chat_assist(message=message, current_context=context)
        return JsonResponse({'success': True, 'reply': reply})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f"Assistant error: {str(e)}"
        }, status=500)

@ensure_csrf_cookie
def chatbot_widget_view(request):
    """
    Renders the standalone chatbot widget template.
    """
    return render(request, 'chatbot/chatbot_widget.html')
