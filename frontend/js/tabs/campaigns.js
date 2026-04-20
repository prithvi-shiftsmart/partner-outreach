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

function previewDrafts() {
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
    return { ...r, message: msg, phone: r.phone_number || r.phone };
  });

  const preview = document.getElementById('camp-preview');
  if (!preview) { console.error('camp-preview element not found'); return; }
  preview.hidden = false;
  let html = '';
  for (const d of drafts.slice(0, 5)) {
    const escapedMsg = esc(d.message).replace(/\n/g, '<br>');
    html += `<div class="camp-preview-item"><strong>${esc(d.first_name || '')} ${esc(d.last_name || '')}</strong> (${esc(d.phone || '')})<br><span class="camp-preview-msg" style="white-space:pre-wrap">${escapedMsg}</span></div>`;
  }
  if (drafts.length > 5) {
    html += `<div class="camp-status">...and ${drafts.length - 5} more</div>`;
  }
  preview.innerHTML = html;
  console.log(`[campaigns] Preview rendered: ${drafts.length} drafts`);

  // Show send section
  document.getElementById('camp-send-section').hidden = false;
}

async function sendBatch() {
  if (drafts.length === 0) return;
  const name = document.getElementById('camp-name').value.trim();
  if (!name) { emit('toast:show', { title: 'Error', body: 'Enter a campaign name' }); return; }
  const teamId = parseInt(document.getElementById('camp-team').value) || 66423;
  const context = document.getElementById('camp-context').value.trim();
  const autoRespond = document.getElementById('camp-auto-respond').checked;

  try {
    const resp = await fetch('/api/messages/batch', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        campaign_name: name, team_id: teamId,
        campaign_context: context || null,
        auto_respond_enabled: autoRespond,
        drafts: drafts.map(d => ({
          phone: d.phone, message: d.message,
          partner_id: d.partner_id || `sm_${d.phone}`,
          first_name: d.first_name || '', last_name: d.last_name || '',
          market: d.market || '', company: d.company_name || d.company || ''
        }))
      })
    });
    const data = await resp.json();
    if (data.success) {
      document.getElementById('camp-batch-progress').hidden = false;
      batchStatus = { total: data.total, sent: 0, errors: 0 };
      updateBatchProgress(batchStatus);
      emit('toast:show', { title: 'Sending', body: `${data.total} messages queued` });

      // Poll for status since batch runs in background
      pollBatchStatus(data.status_file);
    }
  } catch (e) { emit('toast:show', { title: 'Error', body: e.message }); }
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
