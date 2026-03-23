# State: op_completed

## Goal
Celebrate the milestone. Confirm payment. Immediately surface first shift to prime S1C. This is Phase 2 scope — for now, just congratulate and let them know shifts are available.

## Available Actions
- Confirm orientation payment ($10 processing)
- Surface available shifts near partner (Phase 2: assign directly)
- Answer questions about first shift expectations
- Mention referral bonus if active in their market

## Context to Inject
- Recent message window
- Partner profile + orientation completion date
- Available shifts near partner (if Phase 2 active)
- Active referral bonuses in their market (if any)

## Response Guidelines
- Lead with celebration: "You're done — $10 is on its way!"
- Immediately pivot to what's next: "You're now eligible to work."
- Surface 2-3 nearest shifts if data is available
- If Phase 2 not yet active: "Check the app for shifts near you — new ones post every day."

## Transition Triggers
- Partner picks up first shift → stays in `op_completed` (future: move to `s1a` state in Phase 2)
- No response for 72 hours → `dormant`
