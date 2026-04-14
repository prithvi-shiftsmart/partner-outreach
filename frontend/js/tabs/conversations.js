/**
 * Conversations tab — sidebar list + chat panel.
 */

import { store, on, emit, setConversations, setActivePartner, setMessages, setDraft } from '../store.js';
import { fetchConversations, fetchThread, fetchCampaigns, sendMessage, triggerDraft, excludePartner, excludeFromCampaign } from '../api.js';
import { sendWS } from '../ws.js';
import { renderThread, appendMessage as appendBubble, renderDraftIndicator } from '../components/chat.js';

// DOM refs (set during init)
let listEl, threadEl, headerEl, composeEl, emptyEl, draftEl, textareaEl;
let campaignFilterEl, daysFilterEl;

export function initConversationsTab() {
  // Cache DOM refs
  listEl = document.getElementById('conversation-list');
  threadEl = document.getElementById('chat-thread');
  headerEl = document.getElementById('partner-header');
  composeEl = document.getElementById('compose-area');
  emptyEl = document.getElementById('conv-empty');
  draftEl = document.getElementById('draft-indicator');
  textareaEl = document.getElementById('compose-text');
  campaignFilterEl = document.getElementById('campaign-filter');
  daysFilterEl = document.getElementById('days-filter');

  // Event subscriptions (debounced to prevent glitchy rapid re-renders)
  let listRenderTimer = null;
  on('conversations:changed', () => {
    clearTimeout(listRenderTimer);
    listRenderTimer = setTimeout(renderConversationList, 100);
  });
  on('messages:changed', () => {
    if (store.activePartnerId) renderChatThread();
  });
  on('activePartner:changed', loadConversation);
  on('draft:updated', (partnerId) => {
    if (partnerId === store.activePartnerId) updateDraftIndicator();
  });
  on('draft:load', (content) => {
    if (textareaEl && content) {
      textareaEl.value = content;
      textareaEl.focus();
      updateSendButton();
    }
  });
  on('unread:changed', renderConversationList);

  // Filter handlers
  campaignFilterEl.addEventListener('change', reloadConversations);
  daysFilterEl.addEventListener('change', () => {
    store.daysFilter = parseInt(daysFilterEl.value);
    reloadConversations();
  });

  // Compose handlers
  textareaEl.addEventListener('input', updateSendButton);
  textareaEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSend();
    }
  });

  document.getElementById('btn-send').addEventListener('click', handleSend);
  document.getElementById('btn-draft').addEventListener('click', handleDraft);
  document.getElementById('btn-skip').addEventListener('click', handleSkip);
  document.getElementById('btn-escalate').addEventListener('click', handleEscalate);

  // Initial load
  loadCampaigns();
  reloadConversations();
}

export function showConversationsTab() {
  // Refresh on tab show
  loadCampaigns();
  reloadConversations();
}

export function hideConversationsTab() {
  // No cleanup needed
}

// ---- Data Loading ----

async function loadCampaigns() {
  try {
    const data = await fetchCampaigns(30);
    // Preserve current selections
    const selected = new Set(Array.from(campaignFilterEl.selectedOptions).map(o => o.value));
    let options = '';
    for (const c of data.campaigns || []) {
      const sel = selected.has(c.id) ? ' selected' : '';
      options += `<option value="${esc(c.id)}"${sel}>${esc(c.id)} (${c.count})</option>`;
    }
    campaignFilterEl.innerHTML = options;
    // Re-apply selections
    if (selected.size > 0) {
      for (const opt of campaignFilterEl.options) {
        if (selected.has(opt.value)) opt.selected = true;
      }
    }
  } catch (e) {
    console.error('Failed to load campaigns:', e);
  }
}

function getSelectedCampaigns() {
  return Array.from(campaignFilterEl.selectedOptions).map(o => o.value).join(',');
}

async function reloadConversations() {
  try {
    const campaigns = getSelectedCampaigns();
    const days = store.daysFilter;
    const data = await fetchConversations(campaigns, days);
    setConversations(data.conversations || []);
  } catch (e) {
    console.error('Failed to load conversations:', e);
    listEl.innerHTML = '<div class="placeholder-text" style="padding:20px;">Failed to load</div>';
  }
}

let _loadingPartner = null;
async function loadConversation(partnerId) {
  if (!partnerId) {
    showEmpty();
    return;
  }
  // Guard against re-entrant calls (setActivePartner emits activePartner:changed)
  if (_loadingPartner === partnerId) return;
  _loadingPartner = partnerId;

  try {
    const data = await fetchThread(partnerId);
    // Check we're still loading the same partner (user may have clicked another)
    if (_loadingPartner !== partnerId) return;
    store.activePartnerId = partnerId;  // Set directly, don't emit (we're already handling it)
    store.activePartner = data.partner;
    setMessages(data.messages || []);

    // Mark as read
    sendWS({ type: 'mark_read', partner_id: partnerId });

    // Show panels
    emptyEl.hidden = true;
    headerEl.hidden = false;
    threadEl.hidden = false;
    composeEl.hidden = false;

    renderPartnerHeader(data.partner);
    renderChatThread();
    updateDraftIndicator();
    textareaEl.value = '';
    updateSendButton();
  } catch (e) {
    console.error('Failed to load conversation:', e);
  } finally {
    if (_loadingPartner === partnerId) _loadingPartner = null;
  }
}

function showEmpty() {
  emptyEl.hidden = false;
  headerEl.hidden = true;
  threadEl.hidden = true;
  composeEl.hidden = true;
}

// ---- Rendering ----

function renderConversationList() {
  const items = Array.from(store.conversations.values());

  // Sort: unread first, then by last_message_at desc
  items.sort((a, b) => {
    const aUnread = store.unreadCounts.by_partner?.[a.partner_id] > 0 ? 1 : 0;
    const bUnread = store.unreadCounts.by_partner?.[b.partner_id] > 0 ? 1 : 0;
    if (bUnread !== aUnread) return bUnread - aUnread;
    return (b.last_message_at || '').localeCompare(a.last_message_at || '');
  });

  if (items.length === 0) {
    listEl.innerHTML = '<div class="placeholder-text" style="padding:20px;">No conversations found</div>';
    return;
  }

  let html = '';
  for (const c of items) {
    const isActive = c.partner_id === store.activePartnerId;
    const unreadCount = store.unreadCounts.by_partner?.[c.partner_id] || 0;
    const isUnread = unreadCount > 0;
    const draft = store.drafts.get(c.partner_id);
    const name = [c.first_name, c.last_name].filter(Boolean).join(' ') || c.phone_number || c.partner_id;

    html += `
      <div class="conv-item ${isActive ? 'conv-item--active' : ''} ${isUnread ? 'conv-item--unread' : ''}"
           data-partner-id="${esc(c.partner_id)}">
        <div class="conv-item__row">
          <span class="conv-item__name">${esc(name)}</span>
          <span class="conv-item__time">${formatTimeShort(c.last_message_at)}</span>
        </div>
        <div class="conv-item__preview">${esc(c.last_message || '')}</div>
        ${c.campaign_id ? `<div class="conv-item__campaign">${esc(c.campaign_id)}</div>` : ''}
        <div class="conv-item__badges">
          ${isUnread ? `<span class="badge badge--unread">${unreadCount}</span>` : ''}
          ${draft?.status === 'ready' || draft?.status === 'cached' ? '<span class="badge badge--draft">Draft</span>' : ''}
        </div>
      </div>
    `;
  }
  listEl.innerHTML = html;

  // Click handlers via delegation
  listEl.onclick = (e) => {
    const item = e.target.closest('.conv-item');
    if (item) {
      const pid = item.dataset.partnerId;
      if (pid !== store.activePartnerId) {
        setActivePartner(pid);
      }
    }
  };
}

function renderPartnerHeader(partner) {
  if (!partner || !headerEl) return;
  const name = [partner.first_name, partner.last_name].filter(Boolean).join(' ') || 'Unknown';
  const campaigns = (partner.campaigns || []).join(', ');
  const pid = partner.bq_partner_id || partner.partner_id;
  const pidShort = pid.length > 12 ? pid.slice(0, 12) + '...' : pid;

  headerEl.innerHTML = `
    <div class="conv-header__top">
      <span class="conv-header__name">${esc(name)}</span>
      <span class="conv-header__phone">${esc(partner.phone_number || '')}</span>
      <span class="badge badge--state">${esc(partner.current_state || '')}</span>
      ${partner.market ? `<span class="conv-header__zone">${esc(partner.market)}</span>` : ''}
    </div>
    <div class="conv-header__bottom">
      ${campaigns ? `<span><span class="conv-header__label">Campaign:</span> <span class="conv-header__value">${esc(campaigns)}</span></span>` : ''}
      <span>
        <span class="conv-header__label">ID:</span>
        <span class="conv-header__id" data-copy="${esc(pid)}" title="Click to copy full ID">${esc(pidShort)}</span>
      </span>
      <div class="conv-header__actions">
        <button class="btn btn--secondary" id="btn-toggle-read" style="font-size:11px;padding:4px 10px;">Mark unread</button>
        <button class="btn btn--danger-soft" id="btn-exclude-campaign" style="font-size:11px;padding:4px 10px;">Remove from campaign</button>
        <div style="position:relative;display:inline-block;">
          <button class="btn btn--danger" id="btn-exclude-global" style="font-size:11px;padding:4px 10px;">Never contact again</button>
        </div>
      </div>
    </div>
  `;

  // Exclusion handlers
  headerEl.querySelector('#btn-exclude-campaign')?.addEventListener('click', () => handleExcludeCampaign(partner));
  headerEl.querySelector('#btn-exclude-global')?.addEventListener('click', (e) => handleExcludeGlobal(e, partner));

  // Mark read/unread toggle
  headerEl.querySelector('#btn-toggle-read')?.addEventListener('click', () => {
    const isUnread = store.unreadCounts.by_partner?.[partner.partner_id] > 0;
    if (isUnread) {
      sendWS({ type: 'mark_read', partner_id: partner.partner_id });
    } else {
      sendWS({ type: 'mark_unread', partner_id: partner.partner_id });
    }
  });
}

function renderChatThread() {
  if (!threadEl) return;
  renderThread(store.messages, threadEl);
}

function updateDraftIndicator() {
  if (!draftEl || !store.activePartnerId) return;
  const draft = store.drafts.get(store.activePartnerId);
  renderDraftIndicator(draftEl, draft?.status, draft?.content);
}

function updateSendButton() {
  const btn = document.getElementById('btn-send');
  if (btn) btn.disabled = !textareaEl?.value?.trim();
}

// ---- Actions ----

async function handleSend() {
  const text = textareaEl?.value?.trim();
  if (!text || !store.activePartnerId) return;

  const btn = document.getElementById('btn-send');
  btn.disabled = true;

  // Optimistic UI: append bubble immediately
  appendBubble({
    id: `local_${Date.now()}`,
    direction: 'outbound',
    content: text,
    timestamp: new Date().toISOString(),
  }, threadEl);
  textareaEl.value = '';

  try {
    await sendMessage(store.activePartnerId, text);
    // Update conversation preview
    store.conversations.get(store.activePartnerId).last_message = text.slice(0, 80);
    store.conversations.get(store.activePartnerId).last_direction = 'outbound';
    renderConversationList();
  } catch (e) {
    console.error('Send failed:', e);
    emit('toast:show', { title: 'Send failed', body: e.message });
  } finally {
    updateSendButton();
  }
}

async function handleDraft() {
  if (!store.activePartnerId) return;
  const btn = document.getElementById('btn-draft');
  btn.disabled = true;
  setDraft(store.activePartnerId, 'drafting');
  updateDraftIndicator();
  try {
    await triggerDraft(store.activePartnerId);
  } catch (e) {
    console.error('Draft trigger failed:', e);
    setDraft(store.activePartnerId, 'error');
    updateDraftIndicator();
  } finally {
    btn.disabled = false;
  }
}

async function handleSkip() {
  if (!store.activePartnerId) return;
  // Mark as read and move to next
  sendWS({ type: 'mark_read', partner_id: store.activePartnerId });

  // Find next unread
  const items = Array.from(store.conversations.values());
  const next = items.find(c =>
    c.partner_id !== store.activePartnerId &&
    (store.unreadCounts.by_partner?.[c.partner_id] > 0)
  );
  if (next) {
    setActivePartner(next.partner_id);
  } else {
    showEmpty();
    setActivePartner(null);
  }
}

async function handleEscalate() {
  if (!store.activePartnerId) return;
  emit('toast:show', { title: 'Escalated', body: 'Flagged for human review' });
  // TODO: POST to escalation endpoint when available
}

async function handleExcludeCampaign(partner) {
  const campaign = partner.campaigns?.[0];
  if (!campaign) {
    emit('toast:show', { title: 'Error', body: 'No campaign found for this partner' });
    return;
  }
  if (!confirm(`Remove ${partner.first_name || 'this partner'} from "${campaign}"?`)) return;
  try {
    await excludeFromCampaign(partner.partner_id, campaign);
    store.conversations.delete(partner.partner_id);
    renderConversationList();
    showEmpty();
    setActivePartner(null);
    emit('toast:show', { title: 'Removed', body: `Removed from ${campaign}` });
  } catch (e) {
    emit('toast:show', { title: 'Error', body: e.message });
  }
}

function handleExcludeGlobal(event, partner) {
  // Show inline reason dropdown
  const existing = document.querySelector('.reason-dropdown');
  if (existing) existing.remove();

  const reasons = ['opt_out', 'wrong_number', 'antagonistic', 'not_a_good_fit', 'duplicate', 'other'];
  const dropdown = document.createElement('div');
  dropdown.className = 'reason-dropdown';

  for (const reason of reasons) {
    const btn = document.createElement('button');
    btn.textContent = reason.replace(/_/g, ' ');
    btn.addEventListener('click', async () => {
      dropdown.remove();
      try {
        await excludePartner(partner.partner_id, reason);
        store.conversations.delete(partner.partner_id);
        renderConversationList();
        showEmpty();
        setActivePartner(null);
        emit('toast:show', { title: 'Blocked', body: `${partner.first_name || 'Partner'} added to never-contact list` });
      } catch (e) {
        emit('toast:show', { title: 'Error', body: e.message });
      }
    });
    dropdown.appendChild(btn);
  }

  // Position below the button
  const rect = event.target.getBoundingClientRect();
  dropdown.style.position = 'fixed';
  dropdown.style.top = `${rect.bottom + 4}px`;
  dropdown.style.right = `${window.innerWidth - rect.right}px`;
  document.body.appendChild(dropdown);

  // Close on outside click
  const close = (e) => {
    if (!dropdown.contains(e.target) && e.target !== event.target) {
      dropdown.remove();
      document.removeEventListener('click', close);
    }
  };
  setTimeout(() => document.addEventListener('click', close), 0);
}

// ---- Helpers ----

function formatTimeShort(ts) {
  if (!ts) return '';
  try {
    // Parse as local time (SQLite timestamps have no timezone)
    const parts = ts.match(/(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):?(\d{2})?/);
    if (!parts) return '';
    const date = new Date(parts[1], parts[2] - 1, parts[3], parts[4], parts[5], parts[6] || 0);
    const now = new Date();
    const diffMin = Math.floor((now - date) / 60000);
    if (diffMin < 0) return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    if (diffMin < 1) return 'now';
    if (diffMin < 60) return `${diffMin}m`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h`;
    const diffDays = Math.floor(diffHr / 24);
    if (diffDays < 7) return `${diffDays}d`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
}

function shortCampaign(name) {
  // Shorten campaign names for badges
  if (!name) return '';
  // Remove date prefix like "4.9.26 - "
  const cleaned = name.replace(/^\d+\.\d+\.?\d*\s*-\s*/, '');
  return cleaned.length > 20 ? cleaned.slice(0, 20) + '...' : cleaned;
}

function esc(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}
