# Post-Orientation Shift Outreach Template

## Campaign: referral_low_dl
## Variables: {first_name}, {company}, {market}, {referrer_bonus}, {referee_bonus}

## Prod home note
This template's production counterpart does NOT live in the concierge-new-download module. It lives in `applications/marketplace-api/src/modules/concierge-orientation-passed/llm/prompts/message-templates/post-op-shift.prompt.ts` (the orientation-passed module), since it fires after OP completion. This local file is kept here for continuity with the local funnel-stage layout, but treat the orientation-passed module as the prod source of truth for this template.

## Message (post-OP, with referral context)
Nice work finishing your orientation, {first_name}! You're now eligible to pick up shifts{company_suffix}.

Know anyone who'd want to earn some extra money? You'll get ${referrer_bonus} for each person you refer who completes their first shift, and they'll get ${referee_bonus} too.

Want me to show you what shifts are available near you this week?

## Message (post-OP, no referral)
You're all set, {first_name}! Orientation is done and you're ready to work.

Want me to show you what shifts are available near you this week? Just reply "yes" and I'll pull up what's closest.

## Company suffix rule
- If `company` is known: ` with {company}`
- If unknown: omit entirely (no placeholder)
