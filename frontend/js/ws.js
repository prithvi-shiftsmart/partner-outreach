/**
 * WebSocket client with auto-reconnect and message routing to store.
 */

import { store, updateConversation, setUnreadCounts, setDraft, setSyncStatus, emit } from './store.js';

let ws = null;
let reconnectDelay = 1000;

export function connectWebSocket() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const url = `${proto}://${location.host}/ws`;

  ws = new WebSocket(url);

  ws.onopen = () => {
    console.log('[WS] Connected');
    reconnectDelay = 1000; // Reset backoff
  };

  ws.onmessage = (event) => {
    let data;
    try {
      data = JSON.parse(event.data);
    } catch (e) {
      console.warn('[WS] Invalid message:', event.data);
      return;
    }
    handleMessage(data);
  };

  ws.onclose = () => {
    console.log(`[WS] Disconnected. Reconnecting in ${reconnectDelay / 1000}s...`);
    setTimeout(() => {
      reconnectDelay = Math.min(reconnectDelay * 2, 30000);
      connectWebSocket();
    }, reconnectDelay);
  };

  ws.onerror = (err) => {
    console.error('[WS] Error:', err);
  };
}

export function sendWS(message) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(message));
  }
}

function handleMessage(data) {
  switch (data.type) {

    case 'new_message':
      // Update conversation list
      const updates = {
        last_message: (data.content || '').slice(0, 80),
        last_message_at: data.timestamp,
        last_direction: data.direction,
        unread: data.direction === 'inbound',
      };
      // Only update name if we actually have one — don't overwrite existing
      if (data.partner_name) {
        const parts = data.partner_name.split(' ');
        updates.first_name = parts[0];
        if (parts.length > 1) updates.last_name = parts.slice(1).join(' ');
      }
      updateConversation(data.partner_id, updates);

      // If this is the active conversation, append bubble directly to DOM
      // (don't go through store which triggers full re-render)
      if (store.activePartnerId === data.partner_id) {
        const thread = document.getElementById('chat-thread');
        if (thread) {
          import('./components/chat.js').then(({ appendMessage: appendBubble }) => {
            appendBubble({
              id: `ws_${Date.now()}`,
              direction: data.direction,
              content: data.content,
              timestamp: data.timestamp,
              media_urls: data.media_urls,
              campaign_id: data.campaign_id,
            }, thread);
          });
        }
        // Also add to store.messages for consistency (without emitting)
        store.messages.push({
          id: `ws_${Date.now()}`,
          direction: data.direction,
          content: data.content,
          timestamp: data.timestamp,
          media_urls: data.media_urls,
          campaign_id: data.campaign_id,
        });
      }

      // Show toast for inbound messages
      if (data.direction === 'inbound') {
        const name = data.partner_name || data.phone || 'Unknown';
        emit('toast:show', {
          title: 'New reply',
          body: `${name}: ${(data.content || '').slice(0, 60)}`,
          partnerId: data.partner_id,
        });
      }
      break;

    case 'draft_ready':
      setDraft(data.partner_id, data.cached ? 'cached' : 'ready', data.draft_content);
      break;

    case 'sync_status':
      setSyncStatus(data);
      break;

    case 'unread_update':
      setUnreadCounts(data);
      break;

    case 'batch_progress':
      emit('batch:progress', data);
      break;

    default:
      console.log('[WS] Unknown message type:', data.type);
  }
}
