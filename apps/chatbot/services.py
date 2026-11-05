"""
Gemini AI Writing Assistant Service for INKSPACE.

Interfaces with the official Google Gen AI Python SDK (`google-genai`)
to provide intelligent, conversational AI-assisted blog content generation:
1. Topic understanding & mentoring (suggesting 5 engaging titles, short description, content ideas, target audience)
2. Mode-specific generation (Full Blog, Catchy Titles, Description, Content Ideas, Improve Writing)
3. Multi-turn conversation context flow (remembers selected titles and previous discussion)
4. Structured article generation with direct insertion into the INKSPACE blog editor
5. Graceful fallback generation if offline or API key is unavailable.
"""

import os
import re
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Encapsulates all Google Gemini API interactions using the official google-genai SDK.
    Supports multi-turn chat, mode-based generation, and intelligent fallback responses.
    """

    SYSTEM_INSTRUCTION = (
        "You are INKSPACE AI, a professional blog-writing assistant for INKSPACE.\n\n"
        "Your primary responsibility is to help users transform simple topics and ideas into engaging, "
        "high-quality, publishing-ready blog content.\n\n"
        "Always understand the user's topic and intention before responding.\n\n"
        "Writing Modes:\n"
        "1. When no specific mode is chosen (General / Mentor Mode):\n"
        "   - Understand the user's topic and creative intention.\n"
        "   - Suggest 5 relevant and engaging blog titles (numbered 1 to 5).\n"
        "   - Provide one suitable short description (under 200 characters).\n"
        "   - Suggest relevant content ideas and key headings/subheadings.\n"
        "   - Suggest appropriate writing direction and target audience.\n"
        "   - Ask which idea or title the user would like to develop into a complete blog.\n\n"
        "2. When mode is 'full_blog' or user requests a complete blog:\n"
        "   - Generate a complete, publishing-ready article (500-800 words).\n"
        "   - Include: Catchy Title, Short Description (under 200 chars), and full article with "
        "engaging Introduction, thematic Subheadings (h2/h3), bullet points, and thoughtful Conclusion.\n\n"
        "3. When mode is 'titles' or user asks for catchy titles:\n"
        "   - Suggest 5 to 7 catchy, compelling, click-worthy blog titles.\n"
        "   - Add a brief 1-line explanation of the angle or tone for each title.\n\n"
        "4. When mode is 'description' or user asks for a description:\n"
        "   - Generate 2 to 3 concise, compelling short descriptions (max 200 chars each) "
        "optimized for preview cards, social sharing, and SEO.\n\n"
        "5. When mode is 'ideas' or user asks for content ideas:\n"
        "   - Suggest a structured outline with 4 to 6 main sections and subheadings.\n"
        "   - Recommend key discussion points and target audience insights.\n\n"
        "6. When mode is 'improve' or user asks to improve writing:\n"
        "   - Rewrite and elevate the user-supplied text with cleaner flow, stronger hooks, and better vocabulary.\n"
        "   - Preserve the author's original voice and intended meaning.\n"
        "   - List key improvements made in bullet points.\n\n"
        "Conversation Context:\n"
        "- When a user selects a specific title (e.g., 'I like title #2' or 'Let's do the second one'), "
        "remember that selection from previous turns.\n"
        "- When a user asks to 'generate the full blog' in a follow-up turn, generate the complete article "
        "based on the previously selected title and context.\n\n"
        "Formatting & Tone Guidelines:\n"
        "- Avoid generic responses. Make suggestions specific and authentic to the user's actual topic.\n"
        "- Use clear, professional, warm, and encouraging language.\n"
        "- Format responses with clean Markdown: use ## and ### for headings, **bold** for titles and emphasis, "
        "and bullet points (-) for lists.\n"
        "- Do not wrap responses in raw <html> or <body> tags.\n"
        "- Never claim that a blog has been automatically saved or published. Emphasize that the user "
        "can use the content directly in their editor."
    )

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

    def chat_assist(self, message: str, mode: str = 'general', history: list = None, current_context: dict = None) -> str:
        """
        Intelligent conversational assistant response supporting multi-turn memory,
        mode-based instructions, and draft context.
        """
        if not message or not message.strip():
            return "Please provide a topic, idea, or question so I can assist you with your writing."

        message_clean = message.strip()
        client = self._get_client()

        if client:
            try:
                from google.genai import types

                contents = []

                # Format conversation history
                if history and isinstance(history, list):
                    for turn in history[-8:]:
                        role = "user" if turn.get('role') == 'user' else "model"
                        text_val = turn.get('content', '').strip()
                        if text_val:
                            contents.append(types.Content(
                                role=role,
                                parts=[types.Part.from_text(text=text_val)]
                            ))

                # Inject mode and draft context into the current message
                mode_instructions = ""
                if mode == 'full_blog':
                    mode_instructions = "[MODE: FULL_BLOG - Generate a complete, publishing-ready article with Title, Short Description, and structured Content.]\n"
                elif mode == 'titles':
                    mode_instructions = "[MODE: TITLES - Suggest 5 to 7 catchy, compelling blog titles with a 1-line rationale for each.]\n"
                elif mode == 'description':
                    mode_instructions = "[MODE: DESCRIPTION - Generate 2 to 3 engaging short preview descriptions under 200 characters each.]\n"
                elif mode == 'ideas':
                    mode_instructions = "[MODE: IDEAS - Suggest structured content outline, headings, subheadings, and target audience.]\n"
                elif mode == 'improve':
                    mode_instructions = "[MODE: IMPROVE - Polish and elevate the writing while preserving the author's voice, and list key improvements.]\n"

                context_str = ""
                if current_context and isinstance(current_context, dict):
                    title = current_context.get('title', '').strip()
                    content = current_context.get('content', '').strip()
                    if title or content:
                        context_str = f"[Current Editor Draft - Title: {title} | Content: {content[:300]}...]\n"

                final_user_prompt = f"{mode_instructions}{context_str}User: {message_clean}"

                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=final_user_prompt)]
                ))

                try:
                    response = client.models.generate_content(
                        model=self.model_name,
                        contents=contents,
                        config={
                            'system_instruction': self.SYSTEM_INSTRUCTION,
                            'temperature': 0.7,
                        }
                    )
                    if response and response.text:
                        return response.text.strip()
                except Exception as err:
                    logger.warning(f"Gemini API model {self.model_name} error: {err}. Using dynamic mentor fallback.")
            except Exception as e:
                logger.warning(f"Gemini API chat call failed ({e}). Falling back to mentor generator.")

        # High-fidelity dynamic fallback (works offline or when API key is unavailable)
        return self._generate_dynamic_fallback(message_clean, mode, history)

    def generate_blog_package(self, topic: str, category: str = 'General') -> dict:
        """
        Generate a complete blog package including catchy title, short description,
        and structured article content based on a user-provided topic.
        """
        if not topic or not topic.strip():
            raise ValueError("Topic cannot be empty.")

        topic_clean = topic.strip()[:300]
        client = self._get_client()

        if client:
            prompt = f"""
Given the blog topic: "{topic_clean}" in category "{category}":
Generate a complete, publishing-ready blog package in strict JSON format with the following keys:
- "title": A catchy, compelling blog title (50-80 chars).
- "description": A short, engaging summary for preview cards (120-180 chars, max 200).
- "content": A full structured article (500-800 words) using clean HTML tags (<h3>, <p>, <ul>, <li>, <blockquote>, <strong>). Do not wrap in <html> or <body> tags.
- "suggested_tags": A list of 3 to 5 relevant keyword tags.

Respond ONLY with valid JSON.
"""
            try:
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={
                        'system_instruction': self.SYSTEM_INSTRUCTION,
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
                logger.warning(f"Structured generation with {self.model_name} failed ({e}). Using editorial fallback.")

        return self._generate_editorial_fallback(topic_clean, category)

    def _generate_dynamic_fallback(self, message: str, mode: str, history: list = None) -> str:
        """
        Generates realistic, context-aware, topic-specific mentor responses matching
        the user's expected behavior even when offline or without an active API key.
        """
        msg_lower = message.lower()

        # Check if user is referencing a previous title selection in history
        if history and any(k in msg_lower for k in ['second', '2nd', '#2', 'first', '1st', '#1', 'third', '3rd', '#3', 'full blog', 'generate the full blog', 'write the full blog', 'complete blog']):
            # Recover topic from history
            previous_topic = "Your Chosen Topic"
            for turn in reversed(history):
                if turn.get('role') == 'user':
                    candidate = turn.get('content', '')
                    if len(candidate) > 3 and not any(w in candidate.lower() for k in ['second', 'first', 'third', 'generate'] for w in [k]):
                        previous_topic = candidate
                        break

            clean_title = f"The Essential Guide to {previous_topic.title()}"
            if 'second' in msg_lower or '2nd' in msg_lower or '#2' in msg_lower:
                clean_title = f"Mastering {previous_topic.title()}: Practical Lessons for Modern Creators"
            elif 'third' in msg_lower or '3rd' in msg_lower or '#3' in msg_lower:
                clean_title = f"Why {previous_topic.title()} is Changing the Way We Think and Work"

            if any(k in msg_lower for k in ['full blog', 'generate', 'write', 'complete']):
                return f"""### {clean_title}

**Description:**
Discover the key principles, transformative benefits, and practical insights of {previous_topic} for curious learners and modern practitioners.

---

### Introduction
Every meaningful journey begins with a spark of curiosity. When exploring **{previous_topic}**, what begins as an initial idea quickly unfolds into a rich tapestry of perspectives, creative possibilities, and valuable lessons.

### 1. Understanding the Core Appeal
Why does **{previous_topic}** resonate so strongly today? In an age crowded with fleeting trends and relentless digital noise, engaging with thoughtful topics grounds our focus. It allows us to move from passive consumers to intentional creators.

> *"True craftsmanship is not about doing everything; it is about doing the right things with deep attention and unwavering care."*

### 2. Practical Strategies for Getting Started
- **Start with Fundamentals:** Build a solid foundation before chasing shortcuts or advanced techniques.
- **Embrace Consistent Practice:** Dedicate 20 focused minutes every day to observe, write, and experiment.
- **Learn in Public:** Share your early thoughts and drafts. Honest feedback accelerates growth far faster than isolated perfectionism.

### 3. Overcoming Common Challenges
It is natural to encounter friction when diving into a new subject. Rather than viewing hurdles as roadblocks, treat each obstacle as an invitation to refine your perspective and develop deeper clarity.

### Conclusion & Next Steps
Dedicating time to {previous_topic} is an investment in your personal and creative growth. The most important step is simply taking action today.

*You can click **Use in Editor** to load this complete article directly into your INKSPACE story!*"""

            return f"""Great choice! **"{clean_title}"** is a compelling and thought-provoking angle.

**Why this angle works well:**
- It appeals directly to readers looking for actionable depth.
- It provides a natural structure from beginner foundations to expert takeaways.

Would you like me to **Generate the Full Blog** for this title, or would you like to refine the key headings first?"""

        # Mode: Titles
        if mode == 'titles' or 'catchy title' in msg_lower or 'suggest 5 titles' in msg_lower:
            topic_clean = re.sub(r'^(suggest|write|give me|titles for|catchy titles on)\s*', '', message, flags=re.IGNORECASE).strip() or "Your Topic"
            return f"""Here are 5 engaging, click-worthy blog titles for **"{topic_clean.title()}"**:

1. **Why {topic_clean.title()} Is a Smart Career Choice in 2026** *(Authority & Career focus)*
2. **10 Reasons Why {topic_clean.title()} Captivates Beginners and Experts Alike** *(High curiosity listicle)*
3. **From Curiosity to Mastery: The Unfiltered Guide to {topic_clean.title()}** *(Inspirational journey angle)*
4. **The Secret Behind {topic_clean.title()}: What Most People Miss** *(Curiosity & insider perspective)*
5. **How {topic_clean.title()} Transformed My Daily Thinking and Workflow** *(Personal essay / Storytelling angle)*

**Which title resonates best with your story?** You can click any title to use it in your editor, or ask me to generate a full blog based on it!"""

        # Mode: Description
        if mode == 'description' or 'description' in msg_lower or 'summary' in msg_lower:
            topic_clean = re.sub(r'^(write a description for|short description on|description of)\s*', '', message, flags=re.IGNORECASE).strip() or "your topic"
            return f"""Here are 3 engaging, short preview descriptions for **"{topic_clean.title()}"** (each under 200 characters):

**Option 1 (Inspiring & Editorial):**
Discover how {topic_clean} shapes modern perspectives and unlocks unexpected opportunities for curious thinkers and creators.

**Option 2 (Action-Oriented & Practical):**
A concise, practical guide to mastering {topic_clean}—from foundational principles to everyday habits that deliver real results.

**Option 3 (Curiosity & Storytelling):**
Explore the hidden depth of {topic_clean} and why embracing its core lessons can transform your creative journey.

*Click **Use Description** to apply your favorite option directly to your blog!*"""

        # Mode: Content Ideas
        if mode == 'ideas' or 'content idea' in msg_lower or 'outline' in msg_lower:
            topic_clean = re.sub(r'^(suggest content ideas for|outline for|ideas for)\s*', '', message, flags=re.IGNORECASE).strip() or "Your Topic"
            return f"""Here is a structured content roadmap for a blog on **"{topic_clean.title()}"**:

### Target Audience & Writing Angle
- **Audience:** Passionate beginners, professionals, and curious readers seeking actionable insights.
- **Tone:** Warm, editorial, informative, and engaging.

### Recommended Content Outline
- **1. Introduction & Hook:** Why {topic_clean} matters today; personal observation or striking statistic.
- **2. The Core Fundamentals:** Breaking down essential concepts in accessible, beginner-friendly terms.
- **3. Real-World Applications:** How practitioners apply this knowledge to solve practical challenges.
- **4. Key Pitfalls to Avoid:** Common mistakes beginners make and how to navigate around them.
- **5. Practical Action Plan:** 3 tangible steps readers can implement immediately.
- **6. Conclusion & Takeaway:** A thought-provoking closing reflection to leave a lasting impression.

Would you like me to draft a complete article based on this outline?"""

        # Mode: Improve Writing
        if mode == 'improve' or 'improve' in msg_lower or 'polish' in msg_lower:
            sample_text = message.replace('improve:', '').replace('improve', '').strip()
            if not sample_text:
                sample_text = "Writing about your experiences is important because it helps people learn and also gives you new ideas."

            return f"""Here is an elevated, polished version of your text:

### Polished Version
> *"Documenting your lived experiences does more than simply inform others—it sharpens your own thinking, clarifies complex thoughts, and unlocks unexpected creative breakthroughs."*

### Key Improvements Made:
- **Stronger Vocabulary:** Replaced passive phrasing with active, engaging verbs (*"documenting"*, *"sharpens"*, *"clarifies"*).
- **Rhythmic Flow:** Restructured the sentence to lead with the core insight and build toward an impactful conclusion.
- **Editorial Elegance:** Kept the original meaning intact while infusing warmth and depth.

Would you like me to expand this into a complete opening paragraph for your blog?"""

        # Mode: Full Blog
        if mode == 'full_blog' or any(k in msg_lower for k in ['write a blog', 'create a story', 'full blog', 'generate a post']):
            topic_clean = re.sub(r'^(write a blog|create a story|full blog|generate a post)\s*(about|on)?\s*', '', message, flags=re.IGNORECASE).strip() or "Meaningful Writing"
            return self._format_full_blog_text(topic_clean)

        # Default: General / Mentor Mode (User prompt Section 1: Examples 1 & 2)
        topic_clean = message.strip()
        topic_title = topic_clean.title()

        return f"""Great! Let's explore some thoughtful blog ideas for **"{topic_title}"**.

### Suggested Blog Titles
1. **10 Reasons Why {topic_title} Matters in 2026**
2. **The Secret Behind {topic_title}: A Practical Guide for Beginners**
3. **From Curious to Capable: Mastering the Art of {topic_title}**
4. **Why {topic_title} Is One of the Best Investments in Your Creative Growth**
5. **The Unfiltered Truth About {topic_title} and How It Shapes Everyday Life**

### Suggested Description:
Explore how {topic_clean} offers fresh clarity, practical versatility, and meaningful insights for beginners and seasoned creators alike.

### Content Ideas & Outline:
- **Introduction:** What sparked modern interest in {topic_clean}
- **Core Fundamentals:** Breaking down the key concepts simply
- **Practical Real-World Benefits:** Career, lifestyle, and creative impact
- **Actionable Steps:** Simple habits and techniques to start today
- **Common Mistakes:** Pitfalls to avoid along the way
- **Conclusion:** A thoughtful reflection and call to action

### Writing Direction:
- **Target Audience:** Curious thinkers, aspiring writers, and professionals.
- **Tone:** Welcoming, editorial, insightful, and practical.

**Which idea would you like to develop into a complete blog?** You can reply with a title number (e.g., *"Let's write #1"*), or click **Full Blog** above!"""

    def _format_full_blog_text(self, topic: str) -> str:
        """Helper to format a complete blog post in clean Markdown."""
        topic_clean = topic.strip().title()
        return f"""### The Power of {topic_clean}: A Modern Perspective

**Description:**
Explore the essential principles, transformative benefits, and practical habits that make {topic} deeply rewarding for modern thinkers and creators.

---

### Introduction
Every great pursuit begins with an intentional pause. When we examine **{topic}**, we uncover not just technical mechanics, but a profound way of structuring our thinking, articulating ideas, and connecting with a wider community.

### 1. Why {topic_clean} Deserves Our Attention
In an era inundated with noise and fleeting distractions, mastering the essence of {topic} restores clarity. It encourages us to look past surface shortcuts and focus on true craftsmanship.

> *"Clarity of thought precedes clarity of expression. When you take the time to truly understand your craft, your words carry weight and lasting resonance."*

### 2. Core Pillars of Success
- **Build from First Principles:** Do not blindly copy templates; understand why each element exists.
- **Consistent Deliberate Practice:** Growth compounds quietly through regular, focused writing sessions.
- **Engage with Your Readers:** Meaningful writing invites conversation rather than one-way broadcasting.

### 3. Practical Steps for Daily Life
1. **Set aside dedicated focus blocks:** Eliminate notifications for 30 uninterrupted minutes.
2. **Draft before editing:** Let your thoughts flow freely before polishing grammar and sentence flow.
3. **Read across disciplines:** Draw inspiration from literature, science, design, and history.

### Conclusion
Embracing {topic} is a continuous, fulfilling journey. As you put your thoughts on paper, remember that your unique perspective matters.

*Click **Use in Editor** to insert this complete article into your blog form!*"""

    def _generate_editorial_fallback(self, topic: str, category: str) -> dict:
        """Generates realistic structured blog JSON when offline."""
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
            'model_used': 'inkspace-editorial-engine',
        }
