# Playbook: Keyword Replies (Immediate Response Framework)

**Scope**: How the concierge responds to high-signal one-word replies — HELP, START, and affirmative variants (YES, OK, ready, etc.). These are handled as immediate auto-responses at zero LLM cost by `_config/auto_responses.json`. STOP is handled elsewhere as an opt-out (see guardrails).

## Keyword Map

| Keyword | Partner Intent | Response Strategy |
|---|---|---|
| **HELP** / help / I'm stuck / confused / ? | "I want to be walked through" | Warm, hand-holdy. Affirm you're glad to help, give the entry point, end with a question. |
| **START** / start / ready / YES / OK / sure / let's go / sign me up / do it | "I'm ready now" | Direct, action-first. Entry point only. No trailing question — the CTA *is* the action. |
| **STOP** | Opt-out | Unsubscribe. Handled by guardrails, not this playbook. No further messaging. |

Both HELP and START ultimately point to the same place: the "Unlock nearby shifts" card on the Home tab. Tone is what differs.

## HELP Response — Default Copy

> Happy to walk you through it. Open the Shiftsmart app, go to the Home tab, and look for the "Earn $10 today, unlock shifts" section — tap **Start earning** on the "Unlock nearby shifts" card. Takes about 30 min on your phone and you'll earn $10 at the end. Any questions?

### Context variants
- **Welcome-campaign context (new DL)**: use the default above.
- **Mid-orientation nudge context** (partner is already partway through): *"Happy to help — you can pick up where you left off by opening the 'Unlock nearby shifts' card on the Home tab. What's tripping you up?"*
- **Dormant re-engagement context**: *"Glad you replied. Open the Shiftsmart app, Home tab, and tap 'Start earning' on the 'Unlock nearby shifts' card to begin. What questions can I answer?"*

## START Response — Default Copy

> Open the Shiftsmart app and on the Home tab look for the "Earn $10 today, unlock shifts" section. Tap "Start earning" on the "Unlock nearby shifts" card to begin the In-App Orientation — takes about 30 minutes on your phone and your progress is saved so you can pause and come back. You'll earn $10 when you finish all the steps.

This is the existing auto-response shape already defined in `_config/auto_responses.json` under each campaign's `response`. Keep it short, directive, and action-focused — no trailing question.

### Campaign variants
See `auto_responses.json` for per-campaign variants (e.g. `3.31.26 - continue in-app orientation` uses "pick up where you left off" framing). The default is the new-download entry point.

## Rules

- **Same destination for both**: HELP and START both route to the Home tab "Unlock nearby shifts" card. Don't give partners different entry points based on keyword.
- **Different endings**: HELP ends with a question ("Any questions?", "What's tripping you up?") to keep the conversation open. START ends with the action — no trailing question needed.
- **Plain language**: Never use corporate jargon ("excited to partner with you", "optimize your experience").
- **Short**: Under 3 sentences where possible.
- **No numbered menus**: Don't reply to HELP with "reply 1 for orientation, 2 for pay…" — partners on SMS don't engage with that. Just offer help and ask what they need.
- **State-aware**: If partner state is `mid_orientation` when they reply HELP, use the mid-orientation variant ("pick up where you left off"), not the default entry point copy.
- **State-aware for dormant**: If partner state is `dormant` when they reply HELP, use the dormant re-engagement variant.

## Operator Behavior

- HELP and START replies to any outbound are processed at zero LLM cost — the keyword pre-filter in `auto_responses.json` matches them and the configured response is sent immediately (once `auto_respond_enabled` is on for that campaign).
- If HELP-adjacent intent appears in a *longer* message (e.g., "I need some help figuring out the orientation, what do I do?"), that's NOT an exact-match keyword hit — it goes through the LLM. Use this playbook's tone to draft the situation-specific response.
- Log all keyword-triggered auto-responses with `classified_intent: auto_keyword_{keyword}` so we can measure keyword-driven conversion separately from LLM-handled replies.

## Wiring Status

- **START / affirmative keywords**: wired. `simple_reply_patterns` regex in `auto_responses.json` catches them; `campaigns.<id>.response` is the outbound text.
- **HELP keywords**: content defined in `auto_responses.json` under `help_patterns` + `campaigns.<id>.help_response`, but the three consumers (`server/services/sync_service.py`, `dashboard.py`, `scripts/salesmsg_sync.py`) need a small update to match HELP separately and send the `help_response`. This is a focused ~10-line change per file. See `auto_responses.json` top-level `_note` for the integration contract.
- **STOP**: handled by the platform's unsubscribe mechanism.
