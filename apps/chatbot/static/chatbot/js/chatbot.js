/**
 * INKSPACE Gemini AI Writing Assistant Client Script
 * Handles toggle, messaging, blog generation API calls, and inserting content into editors.
 */

(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', initChatbot);

  function initChatbot() {
    const triggerBtn = document.getElementById('chatbotTriggerBtn');
    const chatbotWindow = document.getElementById('chatbotWindow');
    const closeBtn = document.getElementById('chatbotCloseBtn');
    const minimizeBtn = document.getElementById('chatbotMinimizeBtn');
    const chatbotForm = document.getElementById('chatbotForm');
    const chatbotInput = document.getElementById('chatbotInput');
    const messagesContainer = document.getElementById('chatbotMessages');
    const loadingIndicator = document.getElementById('chatbotLoading');

    if (!triggerBtn || !chatbotWindow) return;

    // Toggle window
    triggerBtn.addEventListener('click', () => {
      chatbotWindow.classList.toggle('d-none');
      if (!chatbotWindow.classList.contains('d-none')) {
        chatbotInput.focus();
        scrollToBottom();
      }
    });

    closeBtn?.addEventListener('click', () => {
      chatbotWindow.classList.add('d-none');
    });

    minimizeBtn?.addEventListener('click', () => {
      chatbotWindow.classList.add('d-none');
    });

    // Quick prompt buttons
    document.querySelectorAll('.quick-prompt-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const prompt = btn.getAttribute('data-prompt');
        chatbotInput.value = prompt;
        chatbotForm.dispatchEvent(new Event('submit', { cancelable: true }));
      });
    });

    // Handle form submission
    chatbotForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const message = chatbotInput.value.trim();
      if (!message) return;

      // Add user message
      appendUserMessage(message);
      chatbotInput.value = '';

      // Check if this looks like a blog generation request
      const isBlogRequest = message.toLowerCase().includes('write a blog') || 
                            message.toLowerCase().includes('create a story') || 
                            message.toLowerCase().includes('full blog') ||
                            message.toLowerCase().includes('generate a post');

      showLoading(true);

      try {
        if (isBlogRequest) {
          // Call structured blog generator
          const topic = message.replace(/^(write a blog|create a story|full blog|generate a post)\s*(about|on)?/i, '').trim() || message;
          const category = document.getElementById('id_category')?.value || 'Technology';

          const res = await fetch('/chatbot/generate-blog/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({ topic, category })
          });

          const data = await res.json();
          if (data.success && data.data) {
            appendStructuredBlogCard(data.data);
          } else {
            appendAssistantMessage(`⚠️ ${data.error || 'Could not generate story. Please try again.'}`);
          }
        } else {
          // Standard chat assistance / advice
          const res = await fetch('/chatbot/chat/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
              message,
              context: {
                title: document.getElementById('id_title')?.value || '',
                content: document.getElementById('id_content')?.value || ''
              }
            })
          });

          const data = await res.json();
          if (data.success && data.reply) {
            appendAssistantMessage(data.reply);
          } else {
            appendAssistantMessage(`⚠️ ${data.error || 'Failed to get response.'}`);
          }
        }
      } catch (err) {
        appendAssistantMessage(`⚠️ Network error: ${err.message}. Please check your connection.`);
      } finally {
        showLoading(false);
        scrollToBottom();
      }
    });

    function appendUserMessage(text) {
      const msgDiv = document.createElement('div');
      msgDiv.className = 'chat-message user-message';
      msgDiv.textContent = text;
      messagesContainer.appendChild(msgDiv);
      scrollToBottom();
    }

    function appendAssistantMessage(text) {
      const wrapper = document.createElement('div');
      wrapper.className = 'chat-message assistant-message d-flex gap-2';
      wrapper.innerHTML = `
        <div class="rounded-circle text-white d-flex align-items-center justify-content-center flex-shrink-0" style="width: 28px; height: 28px; background-color: #C65D24; font-size: 0.75rem;">
          <i class="bi bi-stars"></i>
        </div>
        <div class="message-content p-3 rounded-4 bg-white shadow-xs border text-dark font-sans small" style="max-width: 85%;">
          ${text.replace(/\n/g, '<br>')}
        </div>
      `;
      messagesContainer.appendChild(wrapper);
      scrollToBottom();
    }

    function appendStructuredBlogCard(data) {
      const wrapper = document.createElement('div');
      wrapper.className = 'chat-message assistant-message d-flex gap-2';
      
      const cardHtml = `
        <div class="rounded-circle text-white d-flex align-items-center justify-content-center flex-shrink-0" style="width: 28px; height: 28px; background-color: #C65D24; font-size: 0.75rem;">
          <i class="bi bi-stars"></i>
        </div>
        <div class="message-content p-3 rounded-4 bg-white shadow-xs border text-dark font-sans small w-100" style="max-width: 90%;">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <span class="badge rounded-pill" style="background-color: #FFEDD5; color: #C65D24; font-size: 0.7rem; border: 1px solid #FDBA74;">Draft Ready</span>
            <button class="btn btn-sm btn-orange-outline py-0 px-2 rounded-pill apply-to-editor-btn" style="font-size: 0.72rem;">
              <i class="bi bi-arrow-down-circle me-1"></i> Use in Editor
            </button>
          </div>

          <div class="mb-2 p-2 rounded border" style="background-color: #FFF7ED;">
            <div class="text-muted fw-bold" style="font-size: 0.68rem; text-transform: uppercase;">Title:</div>
            <div class="fw-bold font-serif text-dark blog-card-title">${escapeHtml(data.title)}</div>
          </div>

          <div class="mb-2 p-2 rounded border" style="background-color: #FFF7ED;">
            <div class="text-muted fw-bold" style="font-size: 0.68rem; text-transform: uppercase;">Description:</div>
            <div class="text-secondary small blog-card-desc">${escapeHtml(data.description)}</div>
          </div>

          <div class="p-2 rounded border" style="background-color: #FFF7ED;">
            <div class="text-muted fw-bold mb-1" style="font-size: 0.68rem; text-transform: uppercase;">Content Preview:</div>
            <div class="text-dark small blog-card-content overflow-auto" style="max-height: 120px; font-size: 0.78rem;">
              ${data.content}
            </div>
          </div>
        </div>
      `;

      wrapper.innerHTML = cardHtml;
      messagesContainer.appendChild(wrapper);

      // Bind 'Use in Editor' button
      const useBtn = wrapper.querySelector('.apply-to-editor-btn');
      if (useBtn) {
        useBtn.addEventListener('click', () => {
          const titleInput = document.getElementById('id_title');
          const descInput = document.getElementById('id_description');
          const contentInput = document.getElementById('id_content');

          if (titleInput && descInput && contentInput) {
            titleInput.value = data.title;
            descInput.value = data.description;
            contentInput.value = data.content;

            const countEl = document.getElementById('descCharCount');
            if (countEl) countEl.textContent = `${descInput.value.length}/200`;

            useBtn.innerHTML = '<i class="bi bi-check2"></i> Applied!';
            useBtn.className = 'btn btn-sm btn-orange-primary py-0 px-2 rounded-pill';
          } else {
            alert('Go to the "Write a Blog" page to insert this generated content into the editor!');
          }
        });
      }

      scrollToBottom();
    }

    function showLoading(show) {
      if (loadingIndicator) {
        if (show) loadingIndicator.classList.remove('d-none');
        else loadingIndicator.classList.add('d-none');
      }
    }

    function scrollToBottom() {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function escapeHtml(str) {
      if (!str) return '';
      return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
  }

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

})();
