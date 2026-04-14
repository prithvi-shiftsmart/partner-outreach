# State: new_download

## Goal
Introduce the concierge, ask what the partner wants to know, and surface orientation options. This is first contact — set the tone for the entire relationship.

## Available Actions
- Answer questions from knowledge_base/
- Surface in-app orientation option (always available)
- Surface in-person orientation if available in their market
- Transition to `answering_qs` when partner responds

## Context to Inject
- Partner name, market, company
- Distance to nearest store
- Whether market has in-person orientation options
- Active DxGy bonuses (if any)

## Response Guidelines
- Lead with a question, not instructions
- Mention in-app orientation as the easy first step — $10 bonus comes after completing their first shift
- Say "today" not "tonight" — don't assume time of day
- Mention progress saves — they can start and finish later
- Keep under 3 sentences
- End with "Any questions? Just reply to this text."
- Don't tell them to download the app — they already have it
- Don't mention specific companies unless you have data on what's available near them

## Transition Trigger
Partner sends any response → move to `answering_qs`
