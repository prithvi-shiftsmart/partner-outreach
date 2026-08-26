# DxGy Offer Templates (DL Stage)

## Campaign: dxgy_bonus_offer
## Variables: {first_name}, {bonus_amount}, {required_count}, {window_days}, {deep_link}, {expiry_date}

DL-stage DxGy bonus templates for pre-OP partners. Terms (`{bonus_amount}`, `{required_count}`, `{window_days}`, `{expiry_date}`, `{deep_link}`) come ONLY from the injected `## Active Bonus Offer` block (see `../../../../common/concierge/dxgy-offer-context.md`), never invent them. No em dashes in any variant.

Pre-OP framing throughout: orientation comes first, qualifying shifts only after.

## Variant A — DxGy Follow-Up (CKP)

Sent immediately after the existing welcome message (`welcome-dl.md`, unchanged) when a Circle K DxGy offer is applied. This is a second, separate message, never a replacement for the welcome.

You also have a bonus offer: complete {required_count} Food Prep shifts within {window_days} days and earn ${bonus_amount} on top of your shift pay. Finish your orientation first, then I'll help you find qualifying shifts near you.

Tap here to view your offer: {deep_link}

## Variant B — DxGy Follow-Up (DG)

Sent immediately after the existing welcome message when a Dollar General DxGy offer is applied. Same shape as Variant A, no "Food Prep" mention since DG qualifying shifts aren't role-specific in the same way.

You also have a bonus offer: complete {required_count} shifts within {window_days} days and earn ${bonus_amount} on top of your shift pay. Finish your orientation first, then I'll help you find qualifying shifts near you.

Tap here to view your offer: {deep_link}

## Variant C — Orientation Nudge With Bonus

Weaves the active offer into an orientation nudge. Use in place of (not in addition to) the standard `orientation-nudge.md` variant when the partner has an active offer. Amount/count/window come from the offer context, never hardcode a deal's numbers here.

Hey {first_name}, your orientation is on the home screen of the app. Finish it up and you'll earn {{orientation_payout}} plus be able to start working toward your ${bonus_amount} bonus ({required_count} shifts in {window_days} days). Let me know if you have any questions.

## Variant D — Offer Replacement

Sent when a new offer is applied while the partner's previous offer window was still open. Never restate the old offer's terms, only that it was replaced.

Heads up, {first_name}. You have a new bonus offer that replaces your previous one: complete {required_count} shifts within {window_days} days and earn ${bonus_amount}. Tap here to view it: {deep_link}

## Do Not
- Blend CKP and DG copy in the same message (Food Prep / 14-day / $75 vs generic shifts / 30-day / $50 are never interchangeable, and the numbers should come from context, not be hardcoded here either)
- Send the DxGy follow-up as a replacement for the welcome message, it always comes after
- Reference qualifying shifts as bookable before orientation is done
- Restate a replaced offer's old terms
- Use an em dash anywhere in these templates
