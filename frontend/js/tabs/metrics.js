/**
 * Metrics tab — campaign performance, reply rates, top markets, active batch progress.
 */

import { on } from '../store.js';

let initialized = false;
let pollInterval = null;

export function initMetricsTab() {}

export function showMetricsTab() {
  if (!initialized) {
    initialized = true;
    on('batch:progress', handleBatchProgress);
  }
  loadMetrics();
  loadActiveBatches();
  // Poll active batches every 3s while on this tab
  pollInterval = setInterval(loadActiveBatches, 3000);
}

export function hideMetricsTab() {
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
}

async function loadMetrics() {
  const el = document.querySelector('[data-tab-content="metrics"]');
  const days = el.querySelector('#metrics-days')?.value || 7;

  try {
    const resp = await fetch(`/api/metrics?days=${days}`);
    const data = await resp.json();
    render(el, data, days);
  } catch (e) {
    el.innerHTML = `<div class="placeholder-text">Failed to load metrics: ${e.message}</div>`;
  }
}

async function loadActiveBatches() {
  const container = document.getElementById('active-batches');
  if (!container) return;

  try {
    const resp = await fetch('/api/messages/batches/active');
    const data = await resp.json();
    const batches = data.batches || [];

    if (batches.length === 0) {
      container.innerHTML = '<div class="camp-status">No active sends</div>';
      return;
    }

    let html = '';
    for (const b of batches) {
      const total = b.total || 1;
      const done = (b.sent || 0) + (b.errors || 0);
      const pct = Math.round((done / total) * 100);
      const isDone = b.done;

      html += `
        <div class="batch-item">
          <div class="batch-item__header">
            <span class="batch-item__name">${esc(b.name)}</span>
            <span class="batch-item__stats">${b.sent || 0} sent, ${b.errors || 0} errors / ${total}</span>
          </div>
          <div class="camp-progress-bar">
            <div class="camp-progress-fill ${isDone ? (b.errors > 0 ? 'camp-progress-fill--warn' : 'camp-progress-fill--done') : ''}" style="width:${pct}%"></div>
          </div>
        </div>
      `;
    }
    container.innerHTML = html;
  } catch (e) {
    // Endpoint might not exist yet, that's ok
    container.innerHTML = '';
  }
}

function handleBatchProgress(data) {
  // Real-time update from WebSocket — refresh the batch display
  loadActiveBatches();
}

function render(el, data, days) {
  el.innerHTML = `
    <div class="metrics-layout">
      <div class="metrics-header">
        <h2>Campaign Metrics</h2>
        <select id="metrics-days" class="camp-select" style="width:120px;">
          ${[1,3,7,14,30].map(d => `<option value="${d}" ${d == days ? 'selected' : ''}>${d} day${d>1?'s':''}</option>`).join('')}
        </select>
      </div>

      <div class="metrics-section" style="margin-bottom:16px;">
        <h3>Active Sends</h3>
        <div id="active-batches"><div class="camp-status">Loading...</div></div>
      </div>

      <div class="metrics-cards">
        <div class="metric-card">
          <div class="metric-card__value">${data.outbound_partners}</div>
          <div class="metric-card__label">Partners Messaged</div>
        </div>
        <div class="metric-card">
          <div class="metric-card__value">${data.inbound_partners}</div>
          <div class="metric-card__label">Partners Replied</div>
        </div>
        <div class="metric-card">
          <div class="metric-card__value">${data.reply_rate}%</div>
          <div class="metric-card__label">Reply Rate</div>
        </div>
      </div>

      <div class="metrics-grid">
        <div class="metrics-section">
          <h3>Messages by Campaign</h3>
          <table class="camp-table">
            <thead><tr><th>Campaign</th><th>Status</th><th>Count</th></tr></thead>
            <tbody>
              ${(data.by_campaign || []).map(r => `<tr><td>${esc(r.campaign_id)}</td><td>${esc(r.status)}</td><td>${r.cnt}</td></tr>`).join('')}
            </tbody>
          </table>
        </div>

        <div class="metrics-section">
          <h3>Top Markets</h3>
          <table class="camp-table">
            <thead><tr><th>Market</th><th>Messages</th></tr></thead>
            <tbody>
              ${(data.top_markets || []).map(r => `<tr><td>${esc(r.market)}</td><td>${r.cnt}</td></tr>`).join('')}
            </tbody>
          </table>
        </div>

        <div class="metrics-section">
          <h3>Reply Intent Breakdown</h3>
          <table class="camp-table">
            <thead><tr><th>Intent</th><th>Count</th></tr></thead>
            <tbody>
              ${(data.intents || []).map(r => `<tr><td>${esc(r.classified_intent || 'unclassified')}</td><td>${r.cnt}</td></tr>`).join('')}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;

  el.querySelector('#metrics-days').addEventListener('change', () => loadMetrics());
  // Trigger batch load after render creates the container
  loadActiveBatches();
}

function esc(s) { const d = document.createElement('div'); d.textContent = s||''; return d.innerHTML; }
