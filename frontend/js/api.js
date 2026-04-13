/**
 * REST API fetch wrappers. All return parsed JSON.
 */

async function request(method, url, body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${text.slice(0, 200)}`);
  }
  return res.json();
}

export function fetchConversations(campaigns = '', days = 1) {
  const params = new URLSearchParams({ days });
  if (campaigns) params.set('campaigns', campaigns);
  return request('GET', `/api/conversations?${params}`);
}

export function fetchThread(partnerId) {
  return request('GET', `/api/conversations/${encodeURIComponent(partnerId)}`);
}

export function fetchCampaigns(days = 30) {
  return request('GET', `/api/conversations/campaigns/list?days=${days}`);
}

export function sendMessage(conversationId, message, teamId = 66423) {
  return request('POST', '/api/messages/send', { conversation_id: conversationId, message, team_id: teamId });
}

export function triggerDraft(partnerId, replyId = null) {
  return request('POST', '/api/messages/draft', { partner_id: partnerId, reply_id: replyId });
}

export function excludePartner(partnerId, reason) {
  return request('POST', `/api/excluded/${encodeURIComponent(partnerId)}/exclude`, { reason });
}

export function excludeFromCampaign(partnerId, campaignId) {
  return request('POST', `/api/excluded/${encodeURIComponent(partnerId)}/exclude-campaign`, { campaign_id: campaignId });
}

export function fetchSyncStatus() {
  return request('GET', '/api/sync/status');
}

export function fetchHealth() {
  return request('GET', '/api/health');
}
