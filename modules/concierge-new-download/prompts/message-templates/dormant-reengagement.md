# Dormant Re-Engagement Template

## Campaign: dormant_reengagement
## Variables: {first_name}, {last_touched_step} (optional — which module/step they last touched)

Two A/B variants for partners who went quiet for 48+ hours after a prior outreach. **Send one message only.** If no response, stop and flag for human review — do not auto-send a second dormant nudge. See `_config/funnel_stages/dormant.md` for the state-level rules.

Keyword behavior: see `_config/response_playbook/keyword_replies.md`.

## Variant A — Fresh Angle (no keyword CTA)

Hey {first_name} — checking back in. The In-app orientation is still there when you're ready: 3 steps, about 45 min on your phone, $10 once the background check submits, and it unlocks shifts in your area. No pressure either way.

If you want to pick it up: shiftsmart://explore

Reply STOP to unsubscribe

## Variant B — Reply HELP CTA

Hey {first_name} — didn't want to let this one go quiet. If you're still interested in starting with Circle K, reply **HELP** and I'll walk you through the orientation. If not, reply **STOP** to opt out.

## Variant C — Both-Deal Zone

Hey {first_name} — checking back in. The In-app orientation is still there when you're ready: about 45 min on your phone, $10 once the background check submits, and it unlocks shifts in your area. No pressure either way.

Reply HELP if you want to get started, or STOP to unsubscribe.
