/**
 * Excluded tab — do-not-message partners and campaign exclusions.
 */

import { emit } from '../store.js';

let initialized = false;

export function initExcludedTab() {}

export function showExcludedTab() {
  if (!initialized) initialized = true;
  loadExcluded();
}

export function hideExcludedTab() {}

async function loadExcluded() {
  const el = document.querySelector('[data-tab-content="excluded"]');
  try {
    const resp = await fetch('/api/excluded');
    const data = await resp.json();
    render(el, data.excluded || []);
  } catch (e) {
    el.innerHTML = `<div class="placeholder-text">Failed to load: ${e.message}</div>`;
  }
}

function render(el, partners) {
  const reasons = {};
  for (const p of partners) {
    const r = p.dnm_reason || 'unknown';
    reasons[r] = (reasons[r] || 0) + 1;
  }

  el.innerHTML = `
    <div class="metrics-layout">
      <div class="metrics-header">
        <h2>Excluded Partners (${partners.length})</h2>
      </div>

      <div class="metrics-cards">
        ${Object.entries(reasons).map(([r, c]) => `
          <div class="metric-card">
            <div class="metric-card__value">${c}</div>
            <div class="metric-card__label">${esc(r.replace(/_/g, ' '))}</div>
          </div>
        `).join('')}
      </div>

      <table class="camp-table" style="display:table;">
        <thead><tr>
          <th>Name</th><th>Phone</th><th>Reason</th><th>Excluded</th><th>State</th><th>Actions</th>
        </tr></thead>
        <tbody>
          ${partners.map(p => `
            <tr data-pid="${esc(p.partner_id)}">
              <td>${esc((p.first_name||'') + ' ' + (p.last_name||''))}</td>
              <td>${esc(p.phone_number||'')}</td>
              <td>${esc((p.dnm_reason||'').replace(/_/g, ' '))}</td>
              <td>${esc(p.dnm_at ? p.dnm_at.slice(0, 10) : '')}</td>
              <td>${esc(p.current_state||'')}</td>
              <td><button class="btn btn--secondary reinstate-btn" style="font-size:11px;padding:3px 8px;" data-pid="${esc(p.partner_id)}">Reinstate</button></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;

  // Reinstate handlers
  el.querySelectorAll('.reinstate-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const pid = btn.dataset.pid;
      if (!confirm('Reinstate this partner?')) return;
      try {
        await fetch(`/api/excluded/${encodeURIComponent(pid)}/reinstate`, { method: 'POST' });
        emit('toast:show', { title: 'Reinstated', body: 'Partner removed from excluded list' });
        loadExcluded();
      } catch (e) { emit('toast:show', { title: 'Error', body: e.message }); }
    });
  });
}

function esc(s) { const d = document.createElement('div'); d.textContent = s||''; return d.innerHTML; }
