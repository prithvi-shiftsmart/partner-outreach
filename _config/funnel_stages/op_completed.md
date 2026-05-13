# State: op_completed

## Goal
Celebrate the milestone and immediately surface the 3 best shifts (by quality score) to prime S1C. Preference-based filtering is a fallback, not the primary interaction.

## Available Actions
- Congratulate on finishing orientation
- Show top 3 quality-score shifts with shift cards (including bonus pay if eligible)
- Book a shift on behalf of the partner (Phase 2: assignment API)
- Re-query with preference filter if partner asks (distance / pay / time)
- Answer questions about first shift expectations
- Mention referral bonus if active in their market (as part of opener, before shifts)

## Context to Inject
- Recent message window
- Partner profile + orientation completion date
- Top 3 available shifts near partner ranked by quality score
- Active referral bonuses in their market (if any)
- Bonus pay eligibility per shift

## Response Guidelines
1. Lead with celebration (one line): "Hey {name} — congrats on finishing orientation!"
2. If referral active: one sentence about the referral bonus
3. Immediately show top 3 quality-score shifts using shift card format
4. Book CTA: "Reply 1, 2, or 3 to book."
5. App mention: "You can also browse all open shifts in the app anytime."
6. Soft preference fallback: "If these don't match what you're looking for, let me know what matters most — distance, pay, or time — and I'll pull new options."

## Shift Card Format
Each shift on 3 lines:
- Line 1: `{number}. {Role} — {Sub-type} · ${pay}` (append ` + ${bonus} bonus` if eligible)
- Line 2: `{Day} {M/D} · {start}–{end} · {distance}mi`
- Line 3: `{Brand}, {full street address}`

## Reply Handling
- `1` / `2` / `3` → book that shift
- `more` → re-query top 3, offset by 3
- Partner states a preference (closest, highest pay, time of day) → re-query with that filter, show 3 new shifts
- Free text → LLM interprets intent; clarify if ambiguous

## Transition Triggers
- Partner books first shift → move to `s1a` state (Phase 2)
- No response → nudge cadence: 24h, 3 days, 7 days, 10 days, 14 days (each nudge refreshes top 3 shifts)
- No response for 14 days total → `dormant`
