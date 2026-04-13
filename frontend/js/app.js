/**
 * App entry point — tab routing, initialization.
 */

import { connectWebSocket } from './ws.js';
import { initConversationsTab, showConversationsTab, hideConversationsTab } from './tabs/conversations.js';
import { initCampaignsTab, showCampaignsTab, hideCampaignsTab } from './tabs/campaigns.js';
import { initMetricsTab, showMetricsTab, hideMetricsTab } from './tabs/metrics.js';
import { initExcludedTab, showExcludedTab, hideExcludedTab } from './tabs/excluded.js';
import { initSettingsTab, showSettingsTab, hideSettingsTab } from './tabs/settings.js';
import { initToasts } from './components/toast.js';
import { initBadges } from './components/badge.js';
import { initClipboard } from './components/clipboard.js';

// Tab routing
const tabHandlers = {
  campaigns: { show: showCampaignsTab, hide: hideCampaignsTab },
  conversations: { show: showConversationsTab, hide: hideConversationsTab },
  metrics: { show: showMetricsTab, hide: hideMetricsTab },
  excluded: { show: showExcludedTab, hide: hideExcludedTab },
  settings: { show: showSettingsTab, hide: hideSettingsTab },
};
let activeTab = 'conversations';

function switchTab(name) {
  if (name === activeTab) return;

  // Hide current
  const handler = tabHandlers[activeTab];
  if (handler?.hide) handler.hide();
  document.querySelector(`.tab--active`)?.classList.remove('tab--active');
  document.querySelector(`.tab-content--active`)?.classList.remove('tab-content--active');

  // Show new
  activeTab = name;
  document.querySelector(`.tab[data-tab="${name}"]`)?.classList.add('tab--active');
  document.querySelector(`.tab-content[data-tab-content="${name}"]`)?.classList.add('tab-content--active');
  const newHandler = tabHandlers[name];
  if (newHandler?.show) newHandler.show();
}

// Init
document.querySelectorAll('.tab').forEach(el => {
  el.addEventListener('click', () => switchTab(el.dataset.tab));
});

initToasts();
initBadges();
initClipboard();
initConversationsTab();
connectWebSocket();

console.log('[App] Partner Outreach Dashboard initialized');
