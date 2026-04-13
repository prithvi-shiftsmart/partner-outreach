/**
 * Badge updater. Keeps tab badge and per-conversation badges in sync.
 */

import { on, store } from '../store.js';

let tabBadge;

export function initBadges() {
  tabBadge = document.getElementById('tab-badge-conversations');
  on('unread:changed', updateTabBadge);
}

function updateTabBadge() {
  if (!tabBadge) return;
  const count = store.unreadCounts.total_unread || 0;
  tabBadge.textContent = count > 99 ? '99+' : count;
  tabBadge.hidden = count === 0;
}

/**
 * Update an individual badge element.
 */
export function updateBadge(el, count) {
  if (!el) return;
  el.textContent = count > 99 ? '99+' : count;
  el.hidden = count === 0;
}
