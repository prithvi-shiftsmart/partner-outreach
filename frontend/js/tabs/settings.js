/**
 * Settings tab — token management, sync config, gcloud re-auth.
 */

import { emit } from '../store.js';

let initialized = false;

export function initSettingsTab() {}

export function showSettingsTab() {
  if (!initialized) initialized = true;
  loadSettings();
}

export function hideSettingsTab() {}

async function loadSettings() {
  const el = document.querySelector('[data-tab-content="settings"]');
  try {
    const resp = await fetch('/api/settings');
    const data = await resp.json();
    render(el, data);
  } catch (e) {
    el.innerHTML = `<div class="placeholder-text">Failed to load settings: ${e.message}</div>`;
  }
}

function render(el, data) {
  const token = data.token || {};
  const tokenClass = token.expired ? 'metric-card--danger' : 'metric-card--success';

  el.innerHTML = `
    <div class="metrics-layout">
      <div class="metrics-header"><h2>Settings</h2></div>

      <div class="camp-section">
        <h3 class="camp-section__title">Salesmsg API Token</h3>
        <div class="metric-card ${tokenClass}" style="margin-bottom:12px;">
          <div class="metric-card__value" style="font-size:14px;">${token.expired ? 'EXPIRED' : 'Valid'}</div>
          <div class="metric-card__label">${esc(token.expires_display || 'Unknown')}</div>
        </div>
        <div class="camp-row">
          <input type="password" id="settings-token" class="camp-input" placeholder="Paste new Salesmsg token...">
          <button class="btn btn--primary" id="settings-update-token">Update Token</button>
        </div>
      </div>

      <div class="camp-section">
        <h3 class="camp-section__title">Sync</h3>
        <div class="camp-row">
          <button class="btn btn--secondary" id="settings-quick-sync">Quick Sync</button>
          <button class="btn btn--secondary" id="settings-full-sync">Full Sync</button>
        </div>
      </div>
    </div>
  `;

  document.getElementById('settings-update-token').addEventListener('click', async () => {
    const token = document.getElementById('settings-token').value.trim();
    if (!token) return;
    try {
      const resp = await fetch('/api/settings/token', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
      });
      const result = await resp.json();
      if (result.success) {
        emit('toast:show', { title: 'Token updated', body: `Expires: ${result.expires_display || 'unknown'}` });
        loadSettings();
      }
    } catch (e) { emit('toast:show', { title: 'Error', body: e.message }); }
  });

  document.getElementById('settings-quick-sync').addEventListener('click', async () => {
    await fetch('/api/sync/quick', { method: 'POST' });
    emit('toast:show', { title: 'Sync', body: 'Quick sync triggered' });
  });

  document.getElementById('settings-full-sync').addEventListener('click', async () => {
    await fetch('/api/sync/full', { method: 'POST' });
    emit('toast:show', { title: 'Sync', body: 'Full sync triggered' });
  });
}

function esc(s) { const d = document.createElement('div'); d.textContent = s||''; return d.innerHTML; }
