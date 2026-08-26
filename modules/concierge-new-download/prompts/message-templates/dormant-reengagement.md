# Dormant Re-Engagement Template

## Campaign: dormant_reengagement
## Variables: {first_name}, {last_touched_step} (optional — which module/step they last touched), {company} (both-deal zones: the company the partner chose, if any)

Two A/B variants for partners who went quiet for 48+ hours after a prior outreach. **Send one message only.** If no response, stop and flag for human review — do not auto-send a second dormant nudge. See `_config/funnel_stages/dormant.md` for the state-level rules.

Both-deal zone selection rule: if the partner chose a company before going dormant, use Variant C-Chosen (references that company). If they never chose, use Variant C-Neutral (stays company-neutral, offers the choice again compactly).

Per-company orientation duration (never blend the two): Circle K about 45 minutes, Dollar General about 20 to 30 minutes.

Keyword behavior: see `_config/response_playbook/keyword_replies.md`.

## Variant A — Fresh Angle (no keyword CTA)

Hey {first_name}, checking back in. The In-app orientation is still there when you're ready: 4 steps, about 45 min on your phone, {{orientation_payout}} once the background check submits, and it unlocks shifts in your area. No pressure either way.

If you want to pick it up: shiftsmart://explore

Reply STOP to unsubscribe

## Variant B — Reply HELP CTA

Hey {first_name}, didn't want to let this one go quiet. If you're still interested in starting with Circle K, reply **HELP** and I'll walk you through the orientation. If not, reply **STOP** to opt out.

## Variant C-Chosen — Both-Deal Zone, Chose a Company

Hey {first_name}, checking back in. The {company} orientation is still there when you're ready: [about 45 min on your phone for Circle K / about 20 to 30 min on your phone for Dollar General], {{orientation_payout}} once the background check submits, and it unlocks {company} shifts in your area. No pressure either way.

Reply HELP if you want to pick it up, or STOP to unsubscribe.

## Variant C-Neutral — Both-Deal Zone, Never Chose

Hey {first_name}, checking back in. There are still two ways to start earning near you: Circle K (food prep, orientation about 45 min) or Dollar General (shelves and price tags, about 20 to 30 min). Both pay {{orientation_payout}} when you finish the orientation.

Reply 1 for Circle K or 2 for Dollar General, or STOP to unsubscribe.
