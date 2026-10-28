document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.menu-toggle');
  const sidebar = document.querySelector('#sidebar');
  const mobileMenu = window.matchMedia('(max-width: 760px)');
  const syncMenu = () => {
    if (!sidebar || !toggle) return;
    const open = mobileMenu.matches && sidebar.classList.contains('open');
    sidebar.inert = mobileMenu.matches && !open;
    toggle.setAttribute('aria-expanded', String(open));
  };
  mobileMenu.addEventListener('change', () => {
    sidebar?.classList.remove('open');
    syncMenu();
  });
  syncMenu();
  toggle?.addEventListener('click', () => {
    const open = sidebar.classList.toggle('open');
    syncMenu();
    if (open) sidebar.querySelector('a')?.focus();
  });
  document.addEventListener('click', (event) => {
    if (sidebar?.classList.contains('open') && !sidebar.contains(event.target) && !toggle.contains(event.target)) {
      sidebar.classList.remove('open');
      syncMenu();
    }
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      const wasOpen = sidebar?.classList.contains('open');
      sidebar?.classList.remove('open');
      syncMenu();
      if (wasOpen) toggle?.focus();
    }
  });
  const uz = document.documentElement.lang === 'uz';
  document.querySelectorAll('[data-copy]').forEach(button => {
    button.addEventListener('click', async () => {
      const original = button.innerHTML;
      try {
        await navigator.clipboard.writeText(document.getElementById(button.dataset.copy).textContent);
        button.textContent = uz ? 'Nusxalandi ✓' : 'Скопировано ✓';
      } catch {
        button.textContent = uz ? 'Nusxalab bo‘lmadi' : 'Не удалось скопировать';
      }
      setTimeout(() => { button.innerHTML = original; }, 2000);
    });
  });
  document.querySelector('[data-print]')?.addEventListener('click', () => window.print());
  document.querySelectorAll('[data-help]').forEach(button => {
    button.addEventListener('click', () => {
      document.querySelectorAll('[data-help-panel]').forEach(panel => {
        panel.hidden = panel.dataset.helpPanel !== button.dataset.help;
      });
      document.querySelectorAll('[data-help]').forEach(other => other.setAttribute('aria-pressed', String(other === button)));
    });
  });
  document.querySelectorAll('[data-local-note]').forEach(note => {
    const key = `codestart-note-${note.dataset.localNote}`;
    try { note.value = localStorage.getItem(key) || ''; } catch {}
    note.addEventListener('input', () => {
      try { localStorage.setItem(key, note.value); } catch {}
    });
  });
  document.querySelectorAll('[data-code-editor]').forEach(editor => {
    editor.addEventListener('keydown', event => {
      if (event.key === 'Tab' && !event.shiftKey) {
        event.preventDefault();
        const start = editor.selectionStart;
        const end = editor.selectionEnd;
        editor.setRangeText('    ', start, end, 'end');
        editor.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
  });
  const diagnostic = document.querySelector('[data-diagnostic]');
  if (diagnostic) {
    const questions = [...diagnostic.querySelectorAll('[data-question]')];
    const previous = diagnostic.querySelector('[data-prev-question]');
    const next = diagnostic.querySelector('[data-next-question]');
    const finish = diagnostic.querySelector('[data-finish-diagnostic]');
    let index = Math.max(0, Math.min(Number(diagnostic.dataset.startStep) || 0, questions.length - 1));
    const show = () => {
      diagnostic.querySelector('[data-current-step]').value = index;
      questions.forEach((q, i) => { q.hidden = i !== index; });
      previous.disabled = index === 0;
      next.hidden = index === questions.length - 1;
      finish.hidden = index !== questions.length - 1;
      diagnostic.querySelector('[data-question-count]').textContent = `${index + 1} / ${questions.length}`;
      diagnostic.querySelector('[data-question-progress]').style.setProperty('--progress', `${(index + 1) / questions.length * 100}%`);
    };
    previous.addEventListener('click', () => { if (index > 0) index--; show(); });
    next.addEventListener('click', () => { if (index < questions.length - 1) index++; show(); });
    diagnostic.addEventListener('keydown', event => {
      if (event.key === 'Enter' && event.target.matches('input') && index < questions.length - 1) {
        event.preventDefault(); index++; show();
      }
    });
    show();
  }
});

document.querySelector('[data-ai-form]')?.addEventListener('submit', () => {
  const button = document.querySelector('[data-ai-send]');
  button.disabled = true;
  button.setAttribute('aria-busy', 'true');
});
document.querySelector('[data-delete-chat]')?.addEventListener('submit', event => {
  const question = document.documentElement.lang === 'uz' ? 'Suhbatni o\u2018chirish?' : '\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u0434\u0438\u0430\u043b\u043e\u0433?';
  if (!window.confirm(question)) event.preventDefault();
});

const guardedForms = [...document.querySelectorAll('form[data-unsaved-warning]')].map(form => {
  const snapshot = () => JSON.stringify([...new FormData(form)].filter(([name]) => name !== 'csrfmiddlewaretoken'));
  const initial = snapshot();
  let submitting = false;
  form.addEventListener('submit', event => {
    // Other submit listeners can still cancel a submission.
    submitting = true;
    queueMicrotask(() => { if (event.defaultPrevented) submitting = false; });
  });
  window.addEventListener('pageshow', () => { submitting = false; });
  return () => !submitting && snapshot() !== initial;
});
window.addEventListener('beforeunload', event => {
  if (guardedForms.some(isDirty => isDirty())) {
    event.preventDefault();
    event.returnValue = '';
  }
});
