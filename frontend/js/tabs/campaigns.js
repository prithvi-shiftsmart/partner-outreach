/**
 * Campaigns tab — Query → Draft → Send workflow.
 */

import { emit, on } from '../store.js';
import * as api from '../api.js';

let initialized = false;

export function initCampaignsTab() {}

export function showCampaignsTab() {
  if (!initialized) {
    initialized = true;
    render();
    loadQueries();
    loadTemplates();
  }
}

export function hideCampaignsTab() {}

// State
let queries = [];
let templates = [];
let queryResults = [];
let drafts = [];
let batchStatus = null;
let windowCheck = null; // { ok, blocked, unmapped, ok_count, blocked_count, unmapped_count, total }

const STOP_FOOTER = '\n\nReply STOP to unsubscribe.';

function render() {
  const el = document.querySelector('[data-tab-content="campaigns"]');
  el.innerHTML = `
    <div class="campaigns-layout">
      <div class="campaigns-panel">

        <div class="camp-section">
          <h3 class="camp-section__title">1. Query Partners</h3>
          <div class="camp-row">
            <select id="camp-source" class="camp-select">
              <option value="bq">BigQuery Query</option>
              <option value="manual">Manual List</option>
            </select>
          </div>
          <div id="camp-bq-section">
            <div class="camp-row">
              <select id="camp-saved-query" class="camp-select">
                <option value="">Select saved query...</option>
              </select>
            </div>
            <textarea id="camp-sql" class="camp-textarea" rows="6" placeholder="Paste SQL or select a saved query..."></textarea>
            <div class="camp-row">
              <button class="btn btn--primary" id="camp-run-query">Run Query</button>
              <span id="camp-query-status" class="camp-status"></span>
            </div>
          </div>
          <div id="camp-manual-section" hidden>
            <textarea id="camp-manual-list" class="camp-textarea" rows="6" placeholder="first_name, last_name, phone_number (tab or comma separated, one per line)"></textarea>
            <button class="btn btn--primary" id="camp-parse-list">Parse List</button>
          </div>
          <div id="camp-results" class="camp-results" hidden>
            <div class="camp-results__header">
              <span id="camp-result-count">0 partners</span>
            </div>
            <div class="camp-results__table" id="camp-results-table"></div>
          </div>
        </div>

        <div class="camp-section" id="camp-draft-section" hidden>
          <h3 class="camp-section__title">2. Draft Messages</h3>
          <div class="camp-row">
            <select id="camp-template" class="camp-select">
              <option value="">Select template...</option>
              <option value="custom">Custom message</option>
            </select>
          </div>
          <textarea id="camp-message" class="camp-textarea" rows="4" placeholder="Message template. Use {first_name}, {company_name}, {market}..."></textarea>
          <button class="btn btn--secondary" id="camp-preview-btn">Preview Drafts</button>
          <div id="camp-preview" class="camp-preview" hidden></div>
        </div>

        <div class="camp-section" id="camp-send-section" hidden>
          <h3 class="camp-section__title">3. Configure & Send</h3>
          <div class="camp-row">
            <input id="camp-name" class="camp-input" placeholder="Campaign name (e.g., 4.13 - New DL Push)" />
          </div>
          <div class="camp-row">
            <select id="camp-team" class="camp-select"></select>
          </div>
          <textarea id="camp-context" class="camp-textarea" rows="3" placeholder="Campaign context for AI responses (optional)..."></textarea>
          <label class="camp-checkbox">
            <input type="checkbox" id="camp-auto-respond"> Enable auto-respond for this campaign
          </label>
          <div class="camp-row" style="gap:8px;">
            <button class="btn btn--primary" id="camp-send-btn">Send All</button>
            <button class="btn btn--secondary" id="camp-log-btn">Log Only</button>
            <button class="btn btn--secondary" id="camp-export-btn">Export CSV</button>
          </div>
          <div id="camp-batch-progress" hidden>
            <div class="camp-progress-bar"><div class="camp-progress-fill" id="camp-progress-fill"></div></div>
            <span id="camp-progress-text" class="camp-status"></span>
          </div>
        </div>

      </div>
    </div>
  `;

  // Wire events
  document.getElementById('camp-source').addEventListener('change', toggleSource);
  document.getElementById('camp-run-query').addEventListener('click', runQuery);
  document.getElementById('camp-parse-list').addEventListener('click', parseManualList);
  document.getElementById('camp-saved-query').addEventListener('change', loadSavedQuery);
  document.getElementById('camp-template').addEventListener('change', loadTemplate);
  document.getElementById('camp-preview-btn').addEventListener('click', previewDrafts);
  document.getElementById('camp-send-btn').addEventListener('click', sendBatch);
  document.getElementById('camp-log-btn').addEventListener('click', logOnly);
  document.getElementById('camp-export-btn').addEventListener('click', exportCSV);

  // Load teams
  loadTeams();

  // Listen for batch progress from WebSocket
  on('batch:progress', updateBatchProgress);
}

function toggleSource() {
  const source = document.getElementById('camp-source').value;
  document.getElementById('camp-bq-section').hidden = source !== 'bq';
  document.getElementById('camp-manual-section').hidden = source !== 'manual';
}

async function loadQueries() {
  try {
    const resp = await fetch('/api/campaigns/queries');
    const d = await resp.json();
    queries = d.queries || [];
    const select = document.getElementById('camp-saved-query');
    for (const q of queries) {
      const opt = document.createElement('option');
      opt.value = q.filename;
      opt.textContent = q.name;
      select.appendChild(opt);
    }
  } catch (e) { console.error('Failed to load queries:', e); }
}

async function loadTemplates() {
  try {
    const resp = await fetch('/api/campaigns/templates');
    const d = await resp.json();
    templates = d.templates || [];
    const select = document.getElementById('camp-template');
    for (const t of templates) {
      const opt = document.createElement('option');
      opt.value = t.name;
      opt.textContent = t.name;
      select.appendChild(opt);
    }
  } catch (e) { console.error('Failed to load templates:', e); }
}

async function loadTeams() {
  try {
    const resp = await fetch('/api/campaigns/teams');
    const d = await resp.json();
    const select = document.getElementById('camp-team');
    for (const t of d.teams || []) {
      const opt = document.createElement('option');
      opt.value = t.id;
      opt.textContent = t.name;
      select.appendChild(opt);
    }
  } catch (e) { console.error('Failed to load teams:', e); }
}

function loadSavedQuery() {
  const filename = document.getElementById('camp-saved-query').value;
  const q = queries.find(q => q.filename === filename);
  if (q) document.getElementById('camp-sql').value = q.sql;
}

function loadTemplate() {
  const name = document.getElementById('camp-template').value;
  const t = templates.find(t => t.name === name);
  if (t) document.getElementById('camp-message').value = t.content;
}

async function runQuery() {
  const sql = document.getElementById('camp-sql').value.trim();
  if (!sql) return;
  const status = document.getElementById('camp-query-status');
  status.textContent = 'Running...';
  try {
    const resp = await fetch('/api/campaigns/query', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql })
    });
    const data = await resp.json();
    if (data.error) {
      status.textContent = 'Query failed — see details below';
      let errBox = document.getElementById('camp-query-error');
      if (!errBox) {
        errBox = document.createElement('pre');
        errBox.id = 'camp-query-error';
        errBox.style.cssText = 'white-space:pre-wrap;background:#fef2f2;color:#991b1b;border:1px solid #fecaca;border-radius:6px;padding:10px;margin-top:8px;font-size:12px;max-height:240px;overflow:auto;';
        status.parentNode.insertBefore(errBox, status.nextSibling);
      }
      errBox.textContent = data.error;
      console.error('BQ error:', data.error);
      return;
    }
    const oldErr = document.getElementById('camp-query-error');
    if (oldErr) oldErr.remove();
    queryResults = data.rows || [];
    status.textContent = `${queryResults.length} partners found`;
    showResults();
  } catch (e) { status.textContent = `Error: ${e.message}`; }
}

function parseManualList() {
  const text = document.getElementById('camp-manual-list').value.trim();
  if (!text) return;
  queryResults = [];
  for (const line of text.split('\n')) {
    const parts = line.split(/[,\t]+/).map(s => s.trim());
    if (parts.length >= 3) {
      queryResults.push({
        first_name: parts[0], last_name: parts[1],
        phone_number: parts[2], company_name: parts[3] || '',
        market: parts[4] || '', partner_id: `sm_${parts[2]}`
      });
    }
  }
  document.getElementById('camp-query-status').textContent = `${queryResults.length} partners parsed`;
  showResults();
}

function showResults() {
  const el = document.getElementById('camp-results');
  const table = document.getElementById('camp-results-table');
  const count = document.getElementById('camp-result-count');
  el.hidden = false;
  count.textContent = `${queryResults.length} partners`;

  if (queryResults.length === 0) { table.innerHTML = '<div class="camp-status">No results</div>'; return; }

  const cols = Object.keys(queryResults[0]).slice(0, 6);
  let html = '<table class="camp-table"><thead><tr>';
  for (const c of cols) html += `<th>${esc(c)}</th>`;
  html += '</tr></thead><tbody>';
  for (const row of queryResults.slice(0, 20)) {
    html += '<tr>';
    for (const c of cols) html += `<td>${esc(String(row[c] || ''))}</td>`;
    html += '</tr>';
  }
  if (queryResults.length > 20) html += `<tr><td colspan="${cols.length}" class="camp-status">...and ${queryResults.length - 20} more</td></tr>`;
  html += '</tbody></table>';
  table.innerHTML = html;

  // Show draft section
  document.getElementById('camp-draft-section').hidden = false;
}

async function previewDrafts() {
  const template = document.getElementById('camp-message').value;
  if (!template || queryResults.length === 0) return;

  drafts = queryResults.map(r => {
    let msg = template
      .replace(/\{first_name\}/g, r.first_name || '')
      .replace(/\{last_name\}/g, r.last_name || '')
      .replace(/\{company_name\}/g, friendlyCompany(r.company_name || r.company || ''))
      .replace(/\{market\}/g, r.market || '')
      .replace(/\{distance_miles\}/g, r.distance_miles || '')
      .replace(/\{num_modules_completed\}/g, r.num_modules_completed || '');
    // Append STOP footer in preview to match what the backend will actually send.
    msg = msg + STOP_FOOTER;
    return {
      ...r,
      message: msg,
      phone: r.phone_number || r.phone,
      zone_description: r.zone_description || '',
    };
  });

  const preview = document.getElementById('camp-preview');
  if (!preview) { console.error('camp-preview element not found'); return; }
  preview.hidden = false;
  let html = '';
  for (const d of drafts.slice(0, 5)) {
    const escapedMsg = esc(d.message).replace(/\n/g, '<br>');
    const zoneTag = d.zone_description ? ` · <span class="camp-status">${esc(d.zone_description)}</span>` : '';
    html += `<div class="camp-preview-item"><strong>${esc(d.first_name || '')} ${esc(d.last_name || '')}</strong> (${esc(d.phone || '')})${zoneTag}<br><span class="camp-preview-msg" style="white-space:pre-wrap">${escapedMsg}</span></div>`;
  }
  if (drafts.length > 5) {
    html += `<div class="camp-status">...and ${drafts.length - 5} more</div>`;
  }
  preview.innerHTML = html;
  console.log(`[campaigns] Preview rendered: ${drafts.length} drafts`);

  // Show send section, then check quiet-hours window for these recipients.
  document.getElementById('camp-send-section').hidden = false;
  await refreshWindowCheck();
}

async function refreshWindowCheck() {
  const banner = ensureWindowBanner();
  const sendBtn = document.getElementById('camp-send-btn');
  const partners = drafts.map(d => ({ partner_id: d.partner_id || `sm_${d.phone}`, zone_description: d.zone_description || '' }));
  const missingZone = partners.filter(p => !p.zone_description).length;
  if (missingZone > 0) {
    windowCheck = null;
    banner.className = 'camp-window-banner camp-window-banner--error';
    banner.innerHTML = `<strong>${missingZone} of ${partners.length} recipients are missing <code>zone_description</code>.</strong> Update your BQ query to select <code>zone_description</code> (e.g. <code>SELECT ..., sm.zone_description FROM ...</code>) and re-run.`;
    if (sendBtn) sendBtn.disabled = true;
    return;
  }
  try {
    const resp = await fetch('/api/campaigns/check-window', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ partners })
    });
    const data = await resp.json();
    windowCheck = data;
    renderWindowBanner(banner, data);
    if (sendBtn) sendBtn.disabled = (data.ok_count === 0);
  } catch (e) {
    banner.className = 'camp-window-banner camp-window-banner--error';
    banner.textContent = `Window check failed: ${e.message}`;
    if (sendBtn) sendBtn.disabled = false;
  }
}

function ensureWindowBanner() {
  let banner = document.getElementById('camp-window-banner');
  if (!banner) {
    banner = document.createElement('div');
    banner.id = 'camp-window-banner';
    banner.className = 'camp-window-banner';
    banner.style.cssText = 'padding:10px 12px;border-radius:6px;margin-top:10px;font-size:13px;line-height:1.4;';
    const sendSection = document.getElementById('camp-send-section');
    sendSection.insertBefore(banner, sendSection.firstChild.nextSibling);
  }
  return banner;
}

function renderWindowBanner(banner, data) {
  const total = data.total || 0;
  const ok = data.ok_count || 0;
  const blocked = data.blocked_count || 0;
  const unmapped = data.unmapped_count || 0;

  if (ok === total) {
    banner.style.cssText = 'padding:10px 12px;border-radius:6px;margin-top:10px;font-size:13px;line-height:1.4;background:#0d2818;color:#86efac;border:1px solid #166534;';
    banner.innerHTML = `<strong>All ${total} recipients are in their 8 AM – 9 PM local window.</strong>`;
    return;
  }

  if (ok === 0) {
    banner.style.cssText = 'padding:10px 12px;border-radius:6px;margin-top:10px;font-size:13px;line-height:1.4;background:#2a1a1a;color:#fca5a5;border:1px solid #7f1d1d;';
    banner.innerHTML = `<strong>None of the ${total} recipients are in their 8 AM – 9 PM local window right now.</strong> Wait until partners' local time is in window, or run the query against a different cohort.${detailList(data)}`;
    return;
  }

  banner.style.cssText = 'padding:10px 12px;border-radius:6px;margin-top:10px;font-size:13px;line-height:1.4;background:#2a2410;color:#fde68a;border:1px solid #78350f;';
  const parts = [`<strong>${ok} of ${total} recipients are in their 8 AM – 9 PM local window.</strong>`];
  if (blocked > 0) parts.push(`${blocked} outside quiet hours`);
  if (unmapped > 0) parts.push(`${unmapped} with unmapped zone (will be skipped)`);
  banner.innerHTML = parts.join(' · ') + ' &mdash; only in-window recipients will be sent.' + detailList(data);
}

function detailList(data) {
  const rows = [];
  for (const b of (data.blocked || []).slice(0, 8)) {
    const local = (b.local_time || '').slice(11, 16);
    const opens = (b.opens_at || '').slice(0, 16).replace('T', ' ');
    rows.push(`${esc(b.zone_description)} · local ${local} · opens ${opens}`);
  }
  for (const u of (data.unmapped || []).slice(0, 4)) {
    rows.push(`${esc(u.zone_description || '(empty)')} · zone not mapped to a timezone`);
  }
  if (rows.length === 0) return '';
  const more = (data.blocked_count + data.unmapped_count) - rows.length;
  let html = '<details style="margin-top:6px;"><summary style="cursor:pointer;">Show affected recipients</summary><div style="margin-top:6px;padding-left:6px;">';
  for (const r of rows) html += `<div>· ${r}</div>`;
  if (more > 0) html += `<div>· …and ${more} more</div>`;
  html += '</div></details>';
  return html;
}

async function sendBatch() {
  if (drafts.length === 0) return;
  const name = document.getElementById('camp-name').value.trim();
  if (!name) { emit('toast:show', { title: 'Error', body: 'Enter a campaign name' }); return; }
  const teamId = parseInt(document.getElementById('camp-team').value) || 66423;
  const context = document.getElementById('camp-context').value.trim();
  const autoRespond = document.getElementById('camp-auto-respond').checked;

  try {
    // Strip the local STOP_FOOTER preview before posting — backend re-appends it
    // so it's the single source of truth, and we don't want to double-up.
    const stripFooter = (msg) => msg.endsWith(STOP_FOOTER) ? msg.slice(0, -STOP_FOOTER.length) : msg;
    const resp = await fetch('/api/messages/batch', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        campaign_name: name, team_id: teamId,
        campaign_context: context || null,
        auto_respond_enabled: autoRespond,
        drafts: drafts.map(d => ({
          phone: d.phone, message: stripFooter(d.message),
          partner_id: d.partner_id || `sm_${d.phone}`,
          first_name: d.first_name || '', last_name: d.last_name || '',
          market: d.market || '', company: d.company_name || d.company || '',
          zone_description: d.zone_description || ''
        }))
      })
    });
    const data = await resp.json();
    showSendError(null);
    if (data.error) {
      showSendError(data.error);
      return;
    }
    if (data.success) {
      document.getElementById('camp-batch-progress').hidden = false;
      batchStatus = { total: data.total, sent: 0, errors: 0, skipped: data.skipped || 0 };
      updateBatchProgress(batchStatus);
      const skippedNote = data.skipped ? `, ${data.skipped} skipped (outside quiet hours)` : '';
      emit('toast:show', { title: 'Sending', body: `${data.total} messages queued${skippedNote}` });

      // Poll for status since batch runs in background
      pollBatchStatus(data.status_file);
    }
  } catch (e) { emit('toast:show', { title: 'Error', body: e.message }); }
}

function showSendError(msg) {
  let box = document.getElementById('camp-send-error');
  if (!msg) { if (box) box.remove(); return; }
  if (!box) {
    box = document.createElement('pre');
    box.id = 'camp-send-error';
    box.style.cssText = 'white-space:pre-wrap;background:#fef2f2;color:#991b1b;border:1px solid #fecaca;border-radius:6px;padding:10px;margin-top:8px;font-size:12px;max-height:240px;overflow:auto;';
    const sendSection = document.getElementById('camp-send-section');
    sendSection.appendChild(box);
  }
  box.textContent = msg;
}

async function pollBatchStatus(statusFile) {
  const filename = statusFile.split('/').pop().replace('_status.json', '');
  const interval = setInterval(async () => {
    try {
      const resp = await fetch(`/api/messages/batch/${encodeURIComponent(filename)}/status`);
      const data = await resp.json();
      if (data.error) return;
      updateBatchProgress(data);
      if (data.done) {
        clearInterval(interval);
        emit('toast:show', { title: 'Complete', body: `Sent ${data.sent}/${data.total}. Errors: ${data.errors}` });
      }
    } catch (e) { /* ignore polling errors */ }
  }, 3000);
}

function updateBatchProgress(data) {
  const fill = document.getElementById('camp-progress-fill');
  const text = document.getElementById('camp-progress-text');
  if (!fill || !text) return;
  const total = data.total || 1;
  const done = (data.sent || 0) + (data.errors || 0);
  const pct = Math.round((done / total) * 100);
  fill.style.width = `${pct}%`;
  text.textContent = `${data.sent || 0} sent, ${data.errors || 0} errors / ${total} total`;
}

async function logOnly() {
  emit('toast:show', { title: 'Log Only', body: 'Not yet implemented — use Send for now' });
}

function exportCSV() {
  if (drafts.length === 0) return;
  const headers = ['partner_id', 'first_name', 'last_name', 'phone', 'market', 'message'];
  let csv = headers.join(',') + '\n';
  for (const d of drafts) {
    csv += headers.map(h => `"${(d[h] || '').replace(/"/g, '""')}"`).join(',') + '\n';
  }
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `campaign_${Date.now()}.csv`; a.click();
  URL.revokeObjectURL(url);
}

function friendlyCompany(name) {
  return name.replace('Circle K - Premium', 'Circle K')
    .replace('PepsiCo Beverages', 'PepsiCo')
    .replace('PepsiCo Foods', 'Frito-Lay');
}

function esc(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}
