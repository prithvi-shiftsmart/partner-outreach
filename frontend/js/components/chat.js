/**
 * Chat bubble renderer. Renders message threads and draft indicators.
 */

import { emit } from '../store.js';

/**
 * Render full thread in container. Clears existing content.
 */
export function renderThread(messages, container) {
  container.innerHTML = '';
  for (const msg of messages) {
    container.appendChild(createBubble(msg));
  }
  scrollToBottom(container);
}

/**
 * Append a single message bubble.
 */
export function appendMessage(message, container) {
  const wasNearBottom = isNearBottom(container);
  container.appendChild(createBubble(message));
  if (wasNearBottom) scrollToBottom(container);
}

/**
 * Render draft indicator.
 */
export function renderDraftIndicator(el, status, content = null) {
  if (!el) return;
  if (!status) {
    el.innerHTML = '';
    el.className = 'conv-compose__draft';
    return;
  }

  switch (status) {
    case 'pending':
    case 'drafting':
    case 'queued':
      el.className = 'conv-compose__draft conv-compose__draft--loading pulse';
      el.innerHTML = 'Drafting reply...';
      break;
    case 'ready':
    case 'cached':
      el.className = 'conv-compose__draft conv-compose__draft--ready';
      el.innerHTML = `Draft ready ${status === 'cached' ? '(cached) ' : ''}— click to load`;
      el.onclick = () => emit('draft:load', content);
      break;
    case 'error':
      el.className = 'conv-compose__draft conv-compose__draft--error';
      el.innerHTML = 'Draft failed — click Draft Reply to retry';
      el.onclick = null;
      break;
    default:
      el.innerHTML = '';
      el.className = 'conv-compose__draft';
  }
}

function createBubble(msg) {
  const div = document.createElement('div');
  const isOutbound = msg.direction === 'outbound';
  div.className = `bubble bubble--${isOutbound ? 'outbound' : 'inbound'}`;

  let html = '';

  // MMS images
  if (msg.media_urls && msg.media_urls.length > 0) {
    html += '<div class="bubble__media">';
    for (const url of msg.media_urls) {
      html += `<img src="${esc(url)}" alt="MMS" loading="lazy" onclick="window.open(this.src)">`;
    }
    html += '</div>';
  }

  // Text content (escape $ for LaTeX prevention)
  const content = esc(msg.content || '').replace(/\$/g, '&#36;');
  html += `<div class="bubble__content">${content}</div>`;

  // Metadata
  html += '<div class="bubble__meta">';
  html += `<span class="bubble__time">${formatTime(msg.timestamp)}</span>`;
  if (msg.campaign_id && isOutbound) {
    html += `<span class="bubble__campaign">via ${esc(msg.campaign_id)}</span>`;
  }
  if (msg.classified_intent && !isOutbound) {
    html += `<span class="bubble__intent">${esc(msg.classified_intent)}</span>`;
  }
  html += '</div>';

  div.innerHTML = html;
  return div;
}

function formatTime(ts) {
  if (!ts) return '';
  try {
    const date = new Date(ts.replace(' ', 'T'));
    const now = new Date();
    const diffMs = now - date;
    const diffMin = Math.floor(diffMs / 60000);
    const diffHr = Math.floor(diffMs / 3600000);

    if (diffMin < 1) return 'just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHr < 24) return `${diffHr}h ago`;

    // Same year
    if (date.getFullYear() === now.getFullYear()) {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) +
        ' ' + date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    }

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) +
      ' ' + date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  } catch {
    return ts;
  }
}

function isNearBottom(el) {
  return el.scrollHeight - el.scrollTop - el.clientHeight < 100;
}

function scrollToBottom(el) {
  requestAnimationFrame(() => { el.scrollTop = el.scrollHeight; });
}

function esc(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}
