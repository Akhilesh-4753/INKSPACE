/**
 * INKSPACE Intelligent AI Writing Assistant Client Script
 * Features:
 * - Multi-turn conversation context memory
 * - 5 writing modes (Full Blog, Catchy Titles, Description, Content Ideas, Improve Writing)
 * - Auto-growing textarea with scrollbar fix (Enter to send, Shift+Enter for newline)
 * - Safe markdown-to-HTML formatting (headings, numbered titles, bullet points, blockquotes)
 * - One-click integration with blog editor (Title, Description, Content, Copy, Regenerate)
 */

(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', initChatbot);

  function initChatbot() {
    const triggerBtn = document.getElementById('chatbotTriggerBtn');
    const chatbotWindow = document.getElementById('chatbotWindow');
    const closeBtn = document.getElementById('chatbotCloseBtn');
    const minimizeBtn = document.getElementById('chatbotMinimizeBtn');
    const newChatBtn = document.getElementById('chatbotNewChatBtn');
    const chatbotForm = document.getElementById('chatbotForm');
    const chatbotInput = document.getElementById('chatbotInput');
    const chatbotSendBtn = document.getElementById('chatbotSendBtn');
    const messagesContainer = document.getElementById('chatbotMessages');
    const loadingIndicator = document.getElementById('chatbotLoading');
    const modeChips = document.querySelectorAll('.mode-chip');
    const activeModeBanner = document.getElementById('activeModeBanner');
    const activeModeLabel = document.getElementById('activeModeLabel');
    const clearActiveModeBtn = document.getElementById('clearActiveModeBtn');

    if (!triggerBtn || !chatbotWindow) return;

    // Chatbot State
    let conversationHistory = [];
    let activeMode = 'general';
    let lastUserPrompt = '';
    let isSubmitting = false;

    const modeDescriptions = {
      full_blog: { label: 'Full Blog', placeholder: 'Enter a topic to generate a complete article...' },
      titles: { label: 'Catchy Titles', placeholder: 'Enter topic or idea for title suggestions...' },
      description: { label: 'Description', placeholder: 'Enter topic for preview descriptions...' },
      ideas: { label: 'Content Ideas', placeholder: 'Enter topic for content outline & headings...' },
      improve: { label: 'Improve Writing', placeholder: 'Paste the paragraph or draft to polish...' },
      general: { label: 'General / Mentor', placeholder: 'Ask AI Assistant or enter a blog topic...' }
    };

    // Toggle window visibility
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

    // New Chat / Reset Conversation
    newChatBtn?.addEventListener('click', () => {
      resetConversation();
    });

    // Mode Selector Chips
    modeChips.forEach(chip => {
      chip.addEventListener('click', () => {
        const selectedMode = chip.getAttribute('data-mode');
        if (activeMode === selectedMode) {
          // Toggle off
          setMode('general');
        } else {
          setMode(selectedMode);
        }
      });
    });

    clearActiveModeBtn?.addEventListener('click', () => {
      setMode('general');
    });

    function setMode(mode) {
      activeMode = mode;
      modeChips.forEach(c => {
        if (c.getAttribute('data-mode') === mode && mode !== 'general') {
          c.classList.add('active-mode');
        } else {
          c.classList.remove('active-mode');
        }
      });

      if (mode !== 'general' && modeDescriptions[mode]) {
        activeModeBanner?.classList.remove('d-none');
        activeModeBanner?.classList.add('d-flex');
        if (activeModeLabel) activeModeLabel.textContent = modeDescriptions[mode].label;
        chatbotInput.placeholder = modeDescriptions[mode].placeholder;
      } else {
        activeModeBanner?.classList.add('d-none');
        activeModeBanner?.classList.remove('d-flex');
        chatbotInput.placeholder = modeDescriptions.general.placeholder;
      }
      chatbotInput.focus();
    }

    // Bind Quick Starter Prompts
    function bindStarterPrompts() {
      document.querySelectorAll('.starter-prompt-pill').forEach(btn => {
        btn.addEventListener('click', () => {
          const prompt = btn.getAttribute('data-prompt');
          if (prompt) {
            chatbotInput.value = prompt;
            adjustInputHeight();
            chatbotForm.dispatchEvent(new Event('submit', { cancelable: true }));
          }
        });
      });
    }
    bindStarterPrompts();

    // ======================================================
    // INPUT BOX AUTO-GROWING & SCROLLBAR FIX (REQUIREMENT 4)
    // ======================================================
    function adjustInputHeight() {
      chatbotInput.style.height = 'auto';
      const scrollHeight = chatbotInput.scrollHeight;
      const maxHeight = 120;

      if (scrollHeight > maxHeight) {
        chatbotInput.style.height = maxHeight + 'px';
        chatbotInput.classList.add('has-scroll');
        chatbotInput.style.overflowY = 'auto';
      } else {
        const calculatedHeight = Math.max(scrollHeight, 42);
        chatbotInput.style.height = calculatedHeight + 'px';
        chatbotInput.classList.remove('has-scroll');
        chatbotInput.style.overflowY = 'hidden';
      }
    }

    chatbotInput.addEventListener('input', adjustInputHeight);

    // Enter sends message, Shift+Enter inserts newline
    chatbotInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        const text = chatbotInput.value.trim();
        if (text && !isSubmitting) {
          chatbotForm.dispatchEvent(new Event('submit', { cancelable: true }));
        }
      }
    });

    // Form submission handler
    chatbotForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const message = chatbotInput.value.trim();
      if (!message || isSubmitting) return;

      lastUserPrompt = message;

      // Add user message to UI
      appendUserMessage(message);

      // Save to conversation history
      conversationHistory.push({ role: 'user', content: message });
      if (conversationHistory.length > 10) {
        conversationHistory = conversationHistory.slice(-10);
      }

      // Reset and resize input box
      chatbotInput.value = '';
      adjustInputHeight();

      // UI state: submitting
      setSubmittingState(true);

      // Check current editor context if available on page
      const currentContext = {
        title: document.getElementById('id_title')?.value || '',
        description: document.getElementById('id_description')?.value || '',
        content: document.getElementById('id_content')?.value || ''
      };

      try {
        const res = await fetch('/chatbot/chat/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
          },
          body: JSON.stringify({
            message: message,
            mode: activeMode,
            history: conversationHistory.slice(0, -1), // send history prior to current turn
            context: currentContext
          })
        });

        const data = await res.json();
        if (data.success && data.reply) {
          // Record assistant reply in history
          conversationHistory.push({ role: 'assistant', content: data.reply });
          appendAssistantMessage(data.reply, activeMode);
        } else {
          appendErrorMessage(data.error || 'The assistant could not process your request. Please try again.');
        }
      } catch (err) {
        appendErrorMessage(`Network error: ${err.message}. Please check your connection.`);
      } finally {
        setSubmittingState(false);
        scrollToBottom();
      }
    });

    function setSubmittingState(submitting) {
      isSubmitting = submitting;
      if (loadingIndicator) {
        if (submitting) loadingIndicator.classList.remove('d-none');
        else loadingIndicator.classList.add('d-none');
      }
      if (chatbotSendBtn) chatbotSendBtn.disabled = submitting;
      if (chatbotInput) chatbotInput.disabled = submitting;
      if (!submitting) {
        chatbotInput.focus();
      }
    }

    function appendUserMessage(text) {
      const msgDiv = document.createElement('div');
      msgDiv.className = 'chat-message user-message';
      msgDiv.textContent = text;
      messagesContainer.appendChild(msgDiv);
      scrollToBottom();
    }

    function appendAssistantMessage(rawText, mode) {
      const wrapper = document.createElement('div');
      wrapper.className = 'chat-message assistant-message d-flex gap-2';

      const formattedHtml = renderSafeMarkdown(rawText);
      const parsedData = extractBlogComponents(rawText);

      // Action buttons bar
      let actionButtonsHtml = '<div class="d-flex flex-wrap align-items-center gap-1 mt-2 pt-2 border-top">';

      // If a full blog or title/description is detected
      if (parsedData.title) {
        actionButtonsHtml += `
          <button type="button" class="btn btn-sm action-chip apply-title-btn" data-title="${escapeHtml(parsedData.title)}">
            <i class="bi bi-type-h1"></i> Use Title
          </button>
        `;
      }

      if (parsedData.description) {
        actionButtonsHtml += `
          <button type="button" class="btn btn-sm action-chip apply-desc-btn" data-desc="${escapeHtml(parsedData.description)}">
            <i class="bi bi-card-text"></i> Use Description
          </button>
        `;
      }

      if (parsedData.content) {
        actionButtonsHtml += `
          <button type="button" class="btn btn-sm action-chip apply-content-btn">
            <i class="bi bi-file-text"></i> Use Content
          </button>
        `;
      }

      // If full blog is generated, show 'Use All in Editor'
      if (parsedData.title && (parsedData.description || parsedData.content)) {
        actionButtonsHtml += `
          <button type="button" class="btn btn-sm action-chip apply-all-btn" style="background-color: #C65D24; color: #FFFFFF; border-color: #C65D24;">
            <i class="bi bi-arrow-down-circle"></i> Use in Editor
          </button>
        `;
      }

      // Universal Copy and Regenerate
      actionButtonsHtml += `
        <button type="button" class="btn btn-sm copy-mini-btn ms-auto copy-full-btn" title="Copy response to clipboard">
          <i class="bi bi-clipboard"></i> Copy
        </button>
        <button type="button" class="btn btn-sm copy-mini-btn regenerate-btn" title="Generate again">
          <i class="bi bi-arrow-repeat"></i> Regenerate
        </button>
      </div>`;

      wrapper.innerHTML = `
        <div class="rounded-circle text-white d-flex align-items-center justify-content-center flex-shrink-0 shadow-xs" style="width: 30px; height: 30px; background-color: #C65D24; font-size: 0.75rem;">
          <i class="bi bi-stars"></i>
        </div>
        <div class="message-content p-3 rounded-4 bg-white shadow-xs border text-dark font-sans small w-100" style="max-width: 88%;">
          <div class="ai-formatted-text text-dark" style="font-size: 0.86rem;">
            ${formattedHtml}
          </div>
          ${actionButtonsHtml}
        </div>
      `;

      // Store raw content in hidden element for clean copying/insertion
      if (parsedData.content) {
        const hiddenContent = document.createElement('textarea');
        hiddenContent.className = 'd-none hidden-content-holder';
        hiddenContent.value = parsedData.content;
        wrapper.querySelector('.message-content').appendChild(hiddenContent);
      }

      messagesContainer.appendChild(wrapper);
      bindActionButtons(wrapper, rawText, parsedData);
      scrollToBottom();
    }

    function appendErrorMessage(errorText) {
      const wrapper = document.createElement('div');
      wrapper.className = 'chat-message assistant-message d-flex gap-2';
      wrapper.innerHTML = `
        <div class="rounded-circle text-white d-flex align-items-center justify-content-center flex-shrink-0" style="width: 30px; height: 30px; background-color: #DC2626; font-size: 0.75rem;">
          <i class="bi bi-exclamation-triangle-fill"></i>
        </div>
        <div class="message-content p-3 rounded-4 bg-white shadow-xs border border-danger-subtle text-danger font-sans small" style="max-width: 88%;">
          <strong>Assistant Notice:</strong> ${escapeHtml(errorText)}
        </div>
      `;
      messagesContainer.appendChild(wrapper);
      scrollToBottom();
    }

    // ======================================================
    // SAFE MARKDOWN TO HTML PARSER (REQUIREMENT 6)
    // ======================================================
    function renderSafeMarkdown(markdown) {
      if (!markdown) return '';

      // 1. Escape raw HTML entities first to prevent XSS
      let html = escapeHtml(markdown);

      // 2. Parse Headings
      html = html.replace(/^###\s+(.*$)/gim, '<h6 class="fw-bold font-serif text-dark mt-2 mb-1">$1</h6>');
      html = html.replace(/^##\s+(.*$)/gim, '<h5 class="fw-bold font-serif text-dark mt-3 mb-1">$1</h5>');

      // 3. Parse Blockquotes
      html = html.replace(/^\&gt;\s*(.*$)/gim, '<blockquote>$1</blockquote>');

      // 4. Parse Bold and Italic
      html = html.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
      html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="fw-semibold text-dark">$1</strong>');
      html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

      // 5. Parse Numbered Titles / List items: e.g. "1. **Title**" or "1. Title"
      html = html.replace(/^(\d+)\.\s+(.*$)/gim, (match, num, text) => {
        return `
          <div class="d-flex align-items-start gap-2 mb-1.5 title-item-card">
            <span class="badge rounded-circle p-0 d-inline-flex align-items-center justify-content-center flex-shrink-0" style="width: 22px; height: 22px; background-color: #FFEDD5; color: #C65D24; font-size: 0.75rem; font-weight: 700;">${num}</span>
            <div class="flex-grow-1">${text}</div>
          </div>
        `;
      });

      // 6. Parse Bullet Lists: e.g. "- item" or "* item"
      html = html.replace(/^[\-\*]\s+(.*$)/gim, `
        <div class="d-flex align-items-start gap-1 mb-1">
          <i class="bi bi-dot fs-5 line-height-1 flex-shrink-0" style="color: #C65D24; margin-top: -3px;"></i>
          <span>$1</span>
        </div>
      `);

      // 7. Parse Paragraph line breaks
      html = html.replace(/\n\n+/g, '</p><p class="mb-2">');
      html = html.replace(/\n/g, '<br>');

      return `<p class="mb-2">${html}</p>`;
    }

    // Extract Title, Description, and Content from Markdown text
    function extractBlogComponents(text) {
      const result = {
        title: '',
        description: '',
        content: ''
      };

      if (!text) return result;

      // Check for Title: e.g., "### Title" or "Suggested Title: ..."
      const titleMatch = text.match(/^###\s+([^\n]+)/m) || 
                         text.match(/\*\*Suggested Title:?\*\*\s*([^\n]+)/i) ||
                         text.match(/1\.\s+\*\*([^\*]+)\*\*/);
      if (titleMatch && titleMatch[1]) {
        result.title = titleMatch[1].replace(/[\*#]/g, '').trim();
      }

      // Check for Description: e.g., "**Description:** ..." or "**Suggested Description:** ..."
      const descMatch = text.match(/\*\*(?:Suggested )?Description:?\*\*\s*([^\n\r]+)/i);
      if (descMatch && descMatch[1]) {
        result.description = descMatch[1].replace(/[\*#]/g, '').trim();
      }

      // Check for Full Content
      if (text.includes('### Introduction') || text.includes('### 1.') || text.includes('---')) {
        let contentPart = text;
        if (text.includes('---')) {
          contentPart = text.split('---').slice(1).join('---');
        }
        result.content = contentPart.trim();
      }

      return result;
    }

    // ======================================================
    // EDITOR INTEGRATION & BUTTON BINDINGS (REQUIREMENT 8)
    // ======================================================
    function bindActionButtons(container, rawText, parsedData) {
      const titleInput = document.getElementById('id_title');
      const descInput = document.getElementById('id_description');
      const contentInput = document.getElementById('id_content');
      const descCharCount = document.getElementById('descCharCount');

      // 'Use Title' button
      const titleBtn = container.querySelector('.apply-title-btn');
      if (titleBtn) {
        titleBtn.addEventListener('click', () => {
          const title = titleBtn.getAttribute('data-title');
          if (titleInput) {
            titleInput.value = title;
            titleInput.focus();
            showToast('Applied title to blog editor!');
            titleBtn.innerHTML = '<i class="bi bi-check2"></i> Applied!';
          } else {
            copyToClipboard(title, 'Title copied to clipboard!');
          }
        });
      }

      // 'Use Description' button
      const descBtn = container.querySelector('.apply-desc-btn');
      if (descBtn) {
        descBtn.addEventListener('click', () => {
          const desc = descBtn.getAttribute('data-desc');
          if (descInput) {
            descInput.value = desc;
            if (descCharCount) descCharCount.textContent = `${desc.length}/200`;
            descInput.focus();
            showToast('Applied description to blog editor!');
            descBtn.innerHTML = '<i class="bi bi-check2"></i> Applied!';
          } else {
            copyToClipboard(desc, 'Description copied to clipboard!');
          }
        });
      }

      // 'Use Content' button
      const contentBtn = container.querySelector('.apply-content-btn');
      if (contentBtn) {
        contentBtn.addEventListener('click', () => {
          const hiddenContent = container.querySelector('.hidden-content-holder');
          const content = hiddenContent ? hiddenContent.value : (parsedData.content || rawText);
          if (contentInput) {
            contentInput.value = content;
            contentInput.focus();
            showToast('Applied content to editor!');
            contentBtn.innerHTML = '<i class="bi bi-check2"></i> Applied!';
          } else {
            copyToClipboard(content, 'Content copied to clipboard!');
          }
        });
      }

      // 'Use All in Editor' button
      const applyAllBtn = container.querySelector('.apply-all-btn');
      if (applyAllBtn) {
        applyAllBtn.addEventListener('click', () => {
          if (titleInput && descInput && contentInput) {
            if (parsedData.title) titleInput.value = parsedData.title;
            if (parsedData.description) {
              descInput.value = parsedData.description;
              if (descCharCount) descCharCount.textContent = `${parsedData.description.length}/200`;
            }
            if (parsedData.content) contentInput.value = parsedData.content;

            showToast('All story content applied to editor!');
            applyAllBtn.innerHTML = '<i class="bi bi-check2-all"></i> Applied to Editor!';
            applyAllBtn.classList.replace('btn-orange-primary', 'btn-success');
          } else {
            copyToClipboard(rawText, 'Content copied! Go to "Write a Blog" to publish.');
          }
        });
      }

      // 'Copy' button
      const copyBtn = container.querySelector('.copy-full-btn');
      if (copyBtn) {
        copyBtn.addEventListener('click', () => {
          copyToClipboard(rawText, 'Copied response to clipboard!');
          copyBtn.innerHTML = '<i class="bi bi-check2"></i> Copied!';
          setTimeout(() => {
            copyBtn.innerHTML = '<i class="bi bi-clipboard"></i> Copy';
          }, 2000);
        });
      }

      // 'Regenerate' button
      const regenBtn = container.querySelector('.regenerate-btn');
      if (regenBtn) {
        regenBtn.addEventListener('click', () => {
          if (lastUserPrompt && !isSubmitting) {
            chatbotInput.value = lastUserPrompt;
            adjustInputHeight();
            chatbotForm.dispatchEvent(new Event('submit', { cancelable: true }));
          }
        });
      }
    }

    function resetConversation() {
      conversationHistory = [];
      setMode('general');
      messagesContainer.innerHTML = `
        <div class="chat-message assistant-message d-flex gap-2">
          <div class="rounded-circle text-white d-flex align-items-center justify-content-center flex-shrink-0 shadow-xs" style="width: 30px; height: 30px; background-color: #C65D24; font-size: 0.75rem;">
            <i class="bi bi-stars"></i>
          </div>
          <div class="message-content p-3 rounded-4 bg-white shadow-xs border text-dark font-sans small" style="max-width: 88%;">
            <p class="mb-1 fw-bold text-dark font-serif" style="font-size: 0.95rem;">Hello! I'm your AI Writing Mentor.</p>
            <p class="mb-2 text-secondary" style="font-size: 0.82rem; line-height: 1.5;">
              Share any topic or vague idea. I'll help you refine the concept, craft catchy titles, structure key headings, write descriptions, or draft the full blog.
            </p>
            
            <div class="text-muted fw-semibold mb-1" style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.04em;">Quick Starters:</div>
            <div class="d-flex flex-wrap gap-1">
              <button class="btn btn-sm starter-prompt-pill" data-prompt="Need food topic">
                🍲 Food in Kerala
              </button>
              <button class="btn btn-sm starter-prompt-pill" data-prompt="Benefits of learning Python">
                🐍 Benefits of Python
              </button>
              <button class="btn btn-sm starter-prompt-pill" data-prompt="How to build healthy productivity habits">
                ⏳ Productivity Habits
              </button>
            </div>
          </div>
        </div>
      `;
      bindStarterPrompts();
      showToast('New conversation started.');
    }

    function copyToClipboard(text, successMessage) {
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
          showToast(successMessage);
        }).catch(() => {
          fallbackCopyText(text, successMessage);
        });
      } else {
        fallbackCopyText(text, successMessage);
      }
    }

    function fallbackCopyText(text, successMessage) {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.opacity = '0';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      try {
        document.execCommand('copy');
        showToast(successMessage);
      } catch (err) {
        showToast('Unable to copy automatically.');
      }
      document.body.removeChild(textArea);
    }

    function showToast(msg) {
      const existing = document.querySelector('.chatbot-toast');
      if (existing) existing.remove();

      const toast = document.createElement('div');
      toast.className = 'chatbot-toast';
      toast.innerHTML = `<i class="bi bi-info-circle me-1 text-warning"></i> ${escapeHtml(msg)}`;
      chatbotWindow.appendChild(toast);

      setTimeout(() => {
        toast.style.transition = 'opacity 0.3s ease';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
      }, 3000);
    }

    function scrollToBottom() {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
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
