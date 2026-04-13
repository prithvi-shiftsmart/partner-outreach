/**
 * Metrics tab — campaign performance, reply rates, top markets.
 */

let initialized = false;

export function initMetricsTab() {}

export function showMetricsTab() {
  if (!initialized) { initialized = true; }
  loadMetrics();
}

export function hideMetricsTab() {}

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

function render(el, data, days) {
  el.innerHTML = `
    <div class="metrics-layout">
      <div class="metrics-header">
        <h2>Campaign Metrics</h2>
        <select id="metrics-days" class="camp-select" style="width:120px;">
          ${[1,3,7,14,30].map(d => `<option value="${d}" ${d == days ? 'selected' : ''}>${d} day${d>1?'s':''}</option>`).join('')}
        </select>
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
}

function esc(s) { const d = document.createElement('div'); d.textContent = s||''; return d.innerHTML; }
