# State: op_completed

## Goal
Celebrate the milestone. Confirm payment. Immediately surface first shift to prime S1C. This is Phase 2 scope — for now, just congratulate and let them know shifts are available.

## Available Actions
- Remind partner about the $10 bonus they'll get after completing their first shift
- Surface available shifts near partner (Phase 2: assign directly)
- Answer questions about first shift expectations
- Mention referral bonus if active in their market

## Context to Inject
- Recent message window
- Partner profile + orientation completion date
- Available shifts near partner (if Phase 2 active)
- Active referral bonuses in their market (if any)

## Response Guidelines
- Lead with celebration: "You finished the orientation!"
- Immediately pivot to what's next: "You're now eligible to pick up shifts — and you'll get a $10 bonus after your first one."
- Surface 2-3 nearest shifts if data is available
- If Phase 2 not yet active: "Check the app for shifts near you — new ones post every day."

## Transition Triggers
- Partner picks up first shift → stays in `op_completed` (future: move to `s1a` state in Phase 2)
- No response for 72 hours → `dormant`
