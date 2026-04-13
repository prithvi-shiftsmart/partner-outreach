/**
 * Client-side state management with event emitter.
 * All state changes flow through here. UI components subscribe to events.
 */

// Event emitter
const _listeners = new Map();

export function on(event, fn) {
  if (!_listeners.has(event)) _listeners.set(event, new Set());
  _listeners.get(event).add(fn);
}

export function off(event, fn) {
  if (_listeners.has(event)) _listeners.get(event).delete(fn);
}

export function emit(event, data) {
  if (_listeners.has(event)) {
    for (const fn of _listeners.get(event)) {
      try { fn(data); } catch (e) { console.error(`Event handler error [${event}]:`, e); }
    }
  }
}

// State
export const store = {
  // Conversation list: Map<partner_id, ConversationSummary>
  conversations: new Map(),

  // Active conversation
  activePartnerId: null,
  activePartner: null,    // full partner metadata

  // Messages for active conversation: array of Message objects
  messages: [],

  // Campaign list for filters
  campaigns: [],
  selectedCampaigns: new Set(),

  // Days filter
  daysFilter: 1,

  // Unread counts
  unreadCounts: { total_unread: 0, by_partner: {} },

  // Draft states: Map<partner_id, {status, content}>
  drafts: new Map(),

  // Sync status
  syncStatus: null,
};

/**
 * Update conversations list from API response.
 */
export function setConversations(list) {
  store.conversations.clear();
  for (const c of list) {
    store.conversations.set(c.partner_id, c);
  }
  emit('conversations:changed');
}

/**
 * Update a single conversation in the list (e.g., from WebSocket new_message).
 */
export function updateConversation(partnerId, updates) {
  const existing = store.conversations.get(partnerId);
  if (existing) {
    Object.assign(existing, updates);
  } else {
    store.conversations.set(partnerId, { partner_id: partnerId, ...updates });
  }
  emit('conversations:changed');
}

/**
 * Set active conversation.
 */
export function setActivePartner(partnerId, partnerData = null) {
  store.activePartnerId = partnerId;
  store.activePartner = partnerData;
  emit('activePartner:changed', partnerId);
}

/**
 * Set messages for active conversation.
 */
export function setMessages(messages) {
  store.messages = messages;
  emit('messages:changed');
}

/**
 * Append a message to active conversation.
 */
export function appendMessage(message) {
  store.messages.push(message);
  emit('messages:changed');
}

/**
 * Set campaigns list.
 */
export function setCampaigns(campaigns) {
  store.campaigns = campaigns;
  emit('campaigns:changed');
}

/**
 * Update unread counts.
 */
export function setUnreadCounts(counts) {
  store.unreadCounts = counts;
  emit('unread:changed');
}

/**
 * Update draft state for a partner.
 */
export function setDraft(partnerId, status, content = null) {
  store.drafts.set(partnerId, { status, content });
  emit('draft:updated', partnerId);
}

/**
 * Update sync status.
 */
export function setSyncStatus(status) {
  store.syncStatus = status;
  emit('sync:updated', status);
}
