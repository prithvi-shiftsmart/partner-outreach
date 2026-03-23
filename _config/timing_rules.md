# Timing Rules

## When to Run Outreach
- Morning check: 9-10 AM EST (partners are planning their day)
- Reply review: afternoon, as replies come in

## Cooldown Periods
- Welcome/activation messages: 48 hours between messages to same partner
- Orientation nudges: 24 hours after orientation started, then 48 hours if no response
- Post-OP shift push: 24 hours after OP, then 72 hours if no response

## Global Cooldown
- No partner receives more than 3 messages in any 7-day window across all campaigns
- Check: `SELECT COUNT(*) FROM message_log WHERE partner_id = ? AND logged_at > datetime('now', '-7 days')`

## Follow-Up Cadence
- If partner doesn't respond to first message: follow up after 48 hours with a different angle
- If no response to follow-up: back off. Flag for ops review.
- Never send more than 2 unreturned messages in a row

## Inbound Rate Limits (LLM Cost Control)

Partners texting in consume an LLM call per message. Rate limits prevent abuse and control costs.

### Per-Partner Limits
- **10 messages per hour** — if exceeded, respond with: "I'm still here! Give me a few minutes and I'll get back to you." No LLM call.
- **30 messages per day** — if exceeded, respond with: "I've got all your questions noted — I'll follow up with you tomorrow." No LLM call. Flag for human review (could be a real need or could be abuse).
- **Check**: `SELECT COUNT(*) FROM reply_chain WHERE partner_id = ? AND direction = 'inbound' AND logged_at > datetime('now', '-1 hour')`

### Global LLM Budget
- **200 LLM calls per day** across all partner conversations
- If budget hit: queue inbound messages for next-day processing. Notify PK.
- Check: `SELECT COUNT(*) FROM reply_chain WHERE direction = 'inbound' AND logged_at > datetime('now', '-24 hours')`
- This is separate from the BQ query budget (15/day)

### Rapid-Fire Detection
- If a partner sends 5+ messages in under 2 minutes: likely frustration, bot testing, or abuse
- Do NOT call LLM for each one. Wait for them to stop, then respond to the last message with full context.
- Flag for human review.

### Exempt from Limits
- Operator-initiated outreach (we message them first) does not count against their inbound limit
- The keyword pre-filter (`_config/keyword_prefilter.json`) catches obvious patterns at zero LLM cost — those don't count either
