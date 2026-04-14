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
    // Parse as local time (SQLite timestamps have no timezone)
    const parts = ts.match(/(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):?(\d{2})?/);
    if (!parts) return ts;
    const date = new Date(parts[1], parts[2] - 1, parts[3], parts[4], parts[5], parts[6] || 0);
    const now = new Date();
    const diffMs = now - date;
    const diffMin = Math.floor(diffMs / 60000);
    const diffHr = Math.floor(diffMs / 3600000);

    if (diffMin < 0) return formatAbsolute(date, now); // future = clock skew, show absolute
    if (diffMin < 1) return 'just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHr < 24) return `${diffHr}h ago`;

    return formatAbsolute(date, now);
  } catch {
    return ts;
  }
}

function formatAbsolute(date, now) {
  const time = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  if (date.toDateString() === now.toDateString()) return time;
  const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  if (date.getFullYear() !== now.getFullYear()) {
    return `${dateStr}, ${date.getFullYear()} ${time}`;
  }
  return `${dateStr} ${time}`;
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
