"""
Gemini AI Writing Assistant Service for INKSPACE.

This service interfaces with the official Google Gen AI Python SDK (`google-genai`)
to provide AI-assisted blog content generation for the INKSPACE platform:
1. Title generation
2. Short description generation
3. Structured article generation (Introduction, Key Sections, Conclusion)
4. Conversational writing advice and headline suggestions
5. Graceful fallback generation if API key is not configured or offline.
"""

import os
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Encapsulates all Google Gemini API interactions using the official google-genai SDK.
    Includes smart editorial fallbacks so developers can test the full MVT workflow
    even before acquiring a Gemini API key.
    """

    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '') or os.getenv('GEMINI_API_KEY', '')
        self.model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash') or os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        self._client = None

    def _get_client(self):
        """
        Lazily initialize the official Google Gen AI client.
        """
        if not self._client:
            if not self.api_key:
                return None
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                logger.warning(
                    "The official 'google-genai' package is not installed. "
                    "Install with: pip install google-genai"
                )
                return None
            except Exception as e:
                logger.warning(f"Could not initialize Gemini client: {e}")
                return None
        return self._client

    def generate_blog_package(self, topic: str, category: str = 'General') -> dict:
        """
        Generate a complete blog package including catchy title, short description,
        and structured article content based on a user-provided topic.

        Returns a dictionary:
        {
            "title": str,
            "description": str,
            "content": str (HTML/Markdown formatted),
            "suggested_tags": list[str],
            "model_used": str
        }
        """
        if not topic or not topic.strip():
            raise ValueError("Topic cannot be empty.")

        topic_clean = topic.strip()[:300]
        client = self._get_client()

        # If client is configured with a valid key, perform real Gemini inference
        if client:
            system_instruction = (
                "You are an editorial writing assistant for INKSPACE, an elegant, Medium-inspired "
                "blogging platform. You produce well-structured, insightful, engaging articles. "
                "Headings should be punchy and content should feature an engaging intro, "
                "clear thematic sections with subheadings, and a thoughtful conclusion."
            )

            prompt = f"""
Given the blog topic: "{topic_clean}" in category "{category}":
Generate a complete, publishing-ready blog package in strict JSON format with the following keys:
- "title": A catchy, compelling blog title (50-80 chars).
- "description": A short, engaging summary for preview cards (120-180 chars, max 200).
- "content": A full structured article (400-800 words) using clean HTML tags (<h3>, <p>, <ul>, <li>, <blockquote>, <strong>). Do not wrap in <html> or <body> tags.
- "suggested_tags": A list of 3 to 5 relevant keyword tags.

Respond ONLY with valid JSON.
"""
            try:
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={
                        'system_instruction': system_instruction,
                        'response_mime_type': 'application/json',
                        'temperature': 0.7,
                    }
                )

                raw_text = response.text.strip()
                try:
                    data = json.loads(raw_text)
                except json.JSONDecodeError:
                    cleaned = raw_text.replace('```json', '').replace('```', '').strip()
                    data = json.loads(cleaned)

                return {
                    'title': data.get('title', '').strip(),
                    'description': data.get('description', '').strip(),
                    'content': data.get('content', '').strip(),
                    'suggested_tags': data.get('suggested_tags', [category, 'Writing', 'Ideas']),
                    'model_used': self.model_name,
                }
            except Exception as e:
                logger.warning(f"Gemini API call failed ({e}). Falling back to editorial generator.")

        # High-fidelity editorial fallback generator (works offline or when key is not set)
        return self._generate_editorial_fallback(topic_clean, category)

    def chat_assist(self, message: str, current_context: dict = None) -> str:
        """
        Conversational assistant response for interactive writing advice,
        headline ideas, or paragraph refinement.
        """
        if not message or not message.strip():
            return "Please provide a question or topic so I can assist you with your writing."

        message_clean = message.strip()
        client = self._get_client()

        if client:
            context_str = ""
            if current_context:
                title = current_context.get('title', '')
                content = current_context.get('content', '')
                if title or content:
                    context_str = f"\nCurrent Draft Title: {title}\nCurrent Draft Preview: {content[:300]}..."

            prompt = f"""
User asks: {message_clean}
{context_str}

Provide helpful, concise, editorial advice or generated blog snippets.
Format your response with clean Markdown or HTML paragraphs.
"""
            try:
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                if response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini chat failed ({e}). Using conversational fallback.")

        return self._get_conversational_fallback(message_clean)

    def _generate_editorial_fallback(self, topic: str, category: str) -> dict:
        """
        Generates realistic, beautifully formatted editorial content when the Gemini API
        key is not provided or offline.
        """
        title_topic = topic.strip().capitalize()
        title = f"The Art of {title_topic}: Why It Matters in 2026"
        description = f"A thoughtful exploration of {topic.strip()} and the lessons it offers for modern thinkers, creators, and professionals."
        content = f"""<p>When we first encounter <strong>{topic}</strong>, it is tempting to focus purely on surface details. Yet the deeper you immerse yourself, the more you realize how it transforms your thinking and opens doors to unexpected opportunities.</p>

<h3>Why {title_topic} Commands Our Attention</h3>
<p>In a world characterized by relentless digital noise and rapid change, cultivating a genuine appreciation for {topic} gives you clarity and creative focus. It shifts your perspective from passive consumer to intentional practitioner.</p>

<blockquote>"True craftsmanship is not about doing everything; it is about doing the right things with deep attention and unwavering care."</blockquote>

<h3>Key Principles to Keep in Mind</h3>
<ul>
  <li><strong>Start with Fundamentals:</strong> Master the core ideas before pursuing advanced shortcuts.</li>
  <li><strong>Iterate in the Open:</strong> Share early drafts, embrace constructive feedback, and treat mistakes as milestones.</li>
  <li><strong>Connect with Fellow Thinkers:</strong> Communities like INKSPACE thrive when diverse voices exchange genuine insights.</li>
</ul>

<h3>Looking Forward</h3>
<p>Whether you are taking your first steps or refining existing skills, dedicating focused energy to {topic} is a rewarding investment in your creative journey. Write down your observations, refine your drafts, and let your perspective be heard.</p>"""

        return {
            'title': title,
            'description': description,
            'content': content,
            'suggested_tags': [category, 'Writing', 'Creativity', 'Reflections'],
            'model_used': 'inkspace-editorial-engine (set GEMINI_API_KEY in .env for live Gemini 2.5/3.8)',
        }

    def _get_conversational_fallback(self, message: str) -> str:
        """
        Provides helpful conversational replies when offline.
        """
        lower = message.lower()
        if 'title' in lower or 'headline' in lower:
            return """Here are 3 compelling title ideas for your story:

1. **Beyond the Surface: Rethinking Everyday Habits**
2. **The Quiet Revolution: Why Simplicity Wins in 2026**
3. **Small Decisions, Massive Compounding: A Guide to Meaningful Focus**

Which direction best matches the tone of your draft?"""

        if 'description' in lower or 'summary' in lower:
            return """Here is an engaging, 2-sentence summary ready for your preview cards:

*"A thoughtful breakdown of the mental shifts and practical routines that elevate your creative output without burnout."*

Would you like to emphasize a specific angle or key takeaway?"""

        return """I'm your INKSPACE AI writing assistant! I can help you generate complete articles, snappy titles, short descriptions, or polish paragraphs.

Try typing:
- *"Write a blog about the benefits of learning Python"*
- *"Suggest 5 catchy titles for a travel story"*
- *"Write a 2-sentence summary for a productivity article"*"""
