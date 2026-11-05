/**
 * INKSPACE Rich Text Editor
 * Handles visual rich-text formatting (Bold, Italic, Underline, H1, H2, H3, Lists, Blockquotes, Links, Code),
 * maintains text selection, supports keyboard shortcuts (Ctrl+B, Ctrl+I, Ctrl+U),
 * and syncs with the hidden Django form textarea for seamless MVT saving.
 */

(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', initEditor);

  function initEditor() {
    const editor = document.getElementById('editorContent');
    const hiddenTextarea = document.getElementById('id_content');
    const toolbar = document.getElementById('editorToolbar');
    const form = document.getElementById('blogPostForm');

    if (!editor || !hiddenTextarea) return;

    // 1. Initial Content Sync
    // Populate the contenteditable div with initial content from Django model/form
    if (hiddenTextarea.value && hiddenTextarea.value.trim() !== '') {
      editor.innerHTML = hiddenTextarea.value.trim();
    } else if (editor.innerHTML && editor.innerHTML.trim() !== '') {
      hiddenTextarea.value = editor.innerHTML.trim();
    }

    // 2. Synchronize contenteditable div with hidden textarea
    function syncContent() {
      let html = editor.innerHTML.trim();
      const text = editor.innerText.trim();

      // Clean up empty browser artifacts like <p><br></p> or <div><br></div>
      if (!text && (html === '<p><br></p>' || html === '<br>' || html === '<div><br></div>')) {
        html = '';
      }

      hiddenTextarea.value = html;
    }

    editor.addEventListener('input', syncContent);
    editor.addEventListener('blur', syncContent);
    editor.addEventListener('keyup', () => {
      syncContent();
      updateToolbarState();
    });
    editor.addEventListener('mouseup', updateToolbarState);
    editor.addEventListener('paste', () => {
      setTimeout(syncContent, 10);
    });

    if (form) {
      form.addEventListener('submit', () => {
        syncContent();
      });
    }

    // 3. Toolbar Button Event Handlers
    if (toolbar) {
      const buttons = toolbar.querySelectorAll('.editor-btn');

      buttons.forEach(btn => {
        // Crucial: mousedown preventDefault keeps cursor/selection in editor
        btn.addEventListener('mousedown', (e) => {
          e.preventDefault();
        });

        btn.addEventListener('click', (e) => {
          e.preventDefault();
          const action = btn.getAttribute('data-action');
          executeAction(action);
          syncContent();
          updateToolbarState();
        });
      });
    }

    function executeAction(action) {
      editor.focus();

      switch (action) {
        case 'bold':
          document.execCommand('bold', false, null);
          break;

        case 'italic':
          document.execCommand('italic', false, null);
          break;

        case 'underline':
          document.execCommand('underline', false, null);
          break;

        case 'h1':
          toggleBlockFormat('<h1>');
          break;

        case 'h2':
          toggleBlockFormat('<h2>');
          break;

        case 'h3':
          toggleBlockFormat('<h3>');
          break;

        case 'p':
          document.execCommand('formatBlock', false, '<p>');
          break;

        case 'ul':
          document.execCommand('insertUnorderedList', false, null);
          break;

        case 'ol':
          document.execCommand('insertOrderedList', false, null);
          break;

        case 'quote':
          toggleBlockFormat('<blockquote>');
          break;

        case 'link':
          insertHyperlink();
          break;

        case 'code':
          insertCodeSnippet();
          break;

        case 'clear':
          document.execCommand('removeFormat', false, null);
          document.execCommand('formatBlock', false, '<p>');
          break;

        default:
          break;
      }
    }

    function toggleBlockFormat(tag) {
      const currentBlock = document.queryCommandValue('formatBlock').toLowerCase();
      const cleanTag = tag.replace(/[<>]/g, '').toLowerCase();

      if (currentBlock === cleanTag) {
        document.execCommand('formatBlock', false, '<p>');
      } else {
        document.execCommand('formatBlock', false, tag);
      }
    }

    function insertHyperlink() {
      const selection = window.getSelection();
      const hasSelection = selection && !selection.isCollapsed;

      let promptMsg = 'Enter hyperlink URL:';
      if (!hasSelection) {
        promptMsg = 'Enter URL for the link (or select text first):';
      }

      const inputUrl = prompt(promptMsg, 'https://');
      if (inputUrl && inputUrl.trim() && inputUrl.trim() !== 'https://') {
        let validUrl = inputUrl.trim();
        if (!/^https?:\/\//i.test(validUrl) && !/^mailto:/i.test(validUrl)) {
          validUrl = 'https://' + validUrl;
        }

        if (!hasSelection) {
          // If no text was selected, insert link text as URL
          document.execCommand('insertHTML', false, `<a href="${validUrl}" target="_blank" rel="noopener noreferrer">${validUrl}</a>`);
        } else {
          document.execCommand('createLink', false, validUrl);
          // Set target="_blank" and rel="noopener noreferrer" on newly created links
          const links = editor.querySelectorAll('a[href="' + validUrl + '"]');
          links.forEach(a => {
            a.setAttribute('target', '_blank');
            a.setAttribute('rel', 'noopener noreferrer');
          });
        }
      }
    }

    function insertCodeSnippet() {
      const selection = window.getSelection();
      if (!selection || selection.rangeCount === 0) return;

      const selectedText = selection.toString();

      if (selectedText.includes('\n')) {
        // Multi-line code block
        const pre = document.createElement('pre');
        const code = document.createElement('code');
        code.textContent = selectedText;
        pre.appendChild(code);

        const range = selection.getRangeAt(0);
        range.deleteContents();
        range.insertNode(pre);
      } else if (selectedText.length > 0) {
        // Inline code
        const code = document.createElement('code');
        code.textContent = selectedText;

        const range = selection.getRangeAt(0);
        range.deleteContents();
        range.insertNode(code);
      } else {
        // Empty cursor
        document.execCommand('insertHTML', false, '<code>code</code>');
      }
    }

    // 4. Update Toolbar Active States (Visual Indicator for Bold, Italic, Headings, etc.)
    function updateToolbarState() {
      if (!toolbar) return;

      const buttons = toolbar.querySelectorAll('.editor-btn');
      const formatBlockVal = (document.queryCommandValue('formatBlock') || '').toLowerCase();

      buttons.forEach(btn => {
        const action = btn.getAttribute('data-action');
        let isActive = false;

        switch (action) {
          case 'bold':
            isActive = document.queryCommandState('bold');
            break;
          case 'italic':
            isActive = document.queryCommandState('italic');
            break;
          case 'underline':
            isActive = document.queryCommandState('underline');
            break;
          case 'ul':
            isActive = document.queryCommandState('insertUnorderedList');
            break;
          case 'ol':
            isActive = document.queryCommandState('insertOrderedList');
            break;
          case 'h1':
            isActive = formatBlockVal === 'h1';
            break;
          case 'h2':
            isActive = formatBlockVal === 'h2';
            break;
          case 'h3':
            isActive = formatBlockVal === 'h3';
            break;
          case 'quote':
            isActive = formatBlockVal === 'blockquote';
            break;
          default:
            break;
        }

        if (isActive) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
    }

    // 5. Keyboard Shortcuts (Ctrl+B, Ctrl+I, Ctrl+U)
    editor.addEventListener('keydown', (e) => {
      const isCtrlOrCmd = e.ctrlKey || e.metaKey;

      if (isCtrlOrCmd) {
        const key = e.key.toLowerCase();
        if (key === 'b') {
          e.preventDefault();
          executeAction('bold');
          syncContent();
          updateToolbarState();
        } else if (key === 'i') {
          e.preventDefault();
          executeAction('italic');
          syncContent();
          updateToolbarState();
        } else if (key === 'u') {
          e.preventDefault();
          executeAction('underline');
          syncContent();
          updateToolbarState();
        }
      }
    });

    // Expose a helper to safely set content from external scripts (like AI Generator / Chatbot)
    window.setEditorContent = function (htmlContent) {
      if (editor) {
        editor.innerHTML = htmlContent;
        syncContent();
        updateToolbarState();
      }
    };
  }
})();

