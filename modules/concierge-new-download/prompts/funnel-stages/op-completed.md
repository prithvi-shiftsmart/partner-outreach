# State: op_completed (Handoff)

## Purpose
This state detects that a partner has completed orientation while still in the new-download conversation. The new-download agent does NOT handle post-OP interactions — it hands off to the orientation-passed agent.

## What Happens
When the `orientation_passed_event` trigger fires:
1. The router creates a new `orientation_passed` conversation document
2. The router closes the existing `new_download` conversation document (status → `CLOSED`)
3. All subsequent inbound messages from this partner are routed to the **orientation-passed agent**

## If Partner Messages Before Handoff Completes
If a partner messages in this brief window, respond warmly:
- "Hey {name} — congrats on finishing orientation! Your $10 orientation payment is on its way. Give me just a moment and I'll pull up some shifts near you."
- Do NOT attempt to surface shifts or use tools — the orientation-passed agent handles that.

## No Tools Available
This agent has no access to shift lookup or assignment tools. All tool-based interactions happen in the orientation-passed agent.

## Transition
- Automatic → partner is routed to `orientation_passed` agent via the concierge router
