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
    content from a given topic and category for one-click insertion into the editor.
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
            model_used=result.get('model_used', 'gemini-2.5-flash')
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
    POST endpoint: Intelligent conversational AI writing assistant communication.
    Accepts:
      - message: User input prompt or topic
      - mode: Selected writing mode ('general', 'full_blog', 'titles', 'description', 'ideas', 'improve')
      - history: List of recent conversation turns [{'role': 'user'|'assistant', 'content': '...'}]
      - context: Current editor draft state {'title': '...', 'content': '...'}
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON format in request.'}, status=400)

    message = data.get('message', '').strip()
    mode = data.get('mode', 'general').strip().lower()
    history = data.get('history', [])
    context = data.get('context', {})

    if not message:
        return JsonResponse({'success': False, 'error': 'Message cannot be empty.'}, status=400)

    try:
        reply = gemini_service.chat_assist(
            message=message,
            mode=mode,
            history=history,
            current_context=context
        )

        # Audit log
        user = request.user if request.user.is_authenticated else None
        AIGenerationLog.objects.create(
            user=user,
            prompt_summary=f"[{mode}] {message[:200]}",
            model_used=gemini_service.model_name
        )

        return JsonResponse({
            'success': True,
            'reply': reply,
            'mode': mode
        })
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
