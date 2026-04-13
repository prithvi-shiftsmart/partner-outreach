/**
 * Toast notification system. Shows slide-in toasts for new messages.
 */

import { on } from '../store.js';

let container;

export function initToasts() {
  container = document.getElementById('toast-container');
  on('toast:show', showToast);
}

export function showToast({ title = '', body = '', partnerId = null, duration = 5000 }) {
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `
    <span class="toast-title">${esc(title)}</span>
    <span class="toast-body">${esc(body)}</span>
    <span class="toast-time">just now</span>
    ${partnerId ? `<span class="toast-action" data-partner="${esc(partnerId)}">View</span>` : ''}
  `;

  // Click "View" to jump to conversation
  const viewBtn = toast.querySelector('.toast-action');
  if (viewBtn) {
    viewBtn.addEventListener('click', () => {
      // Import dynamically to avoid circular deps
      import('../store.js').then(({ setActivePartner }) => {
        setActivePartner(partnerId);
        // Switch to conversations tab
        document.querySelector('[data-tab="conversations"]')?.click();
      });
      removeToast(toast);
    });
  }

  container.appendChild(toast);

  // Auto-dismiss
  setTimeout(() => removeToast(toast), duration);
}

function removeToast(toast) {
  if (!toast.parentNode) return;
  toast.classList.add('toast--exit');
  toast.addEventListener('animationend', () => toast.remove());
}

function esc(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}
