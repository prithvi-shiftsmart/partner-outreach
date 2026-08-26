# DxGy Progress Templates (OP Stage)

## Campaign: dxgy_lifecycle
## Variables: {first_name}, {bonus_amount}, {required_count}, {window_days}, {completions}, {remaining}, {expiry_date}, {deep_link}

OP-stage DxGy lifecycle templates. Engineering wires the trigger → template mapping (see `48 - DxGy Prompt Update Spec.md` §4), this file owns copy only. Progress numbers (`{completions}`, `{remaining}`) MUST come from a fresh `payment_bonuses_tool` call (see `../../../payment-bonuses-tools/payment-bonuses-tool.md`) taken the same turn, never assumed or carried over from a prior turn.

No em dashes in any variant.

## Shift Card Format

Any shift list in these templates uses the standard 4-line card from `../funnel-stages/op-completed.md`, up to 3 shifts, numbered 1-3, only commas and parentheses as separators (no em dash, middle dot, bullet, or pipe):

```
{N}. {Role}, {Pay total} ({Hourly}/hr)[ +${Bonus} bonus][ (Counts toward bonus)]
{Weekday M/D}, {Start-End time}, {Distance} mi
{Brand}
{Full street address}, {City}, {ST}
```

Append `(Counts toward bonus)` to line 1 ONLY for shifts matching the offer's `qualifying_filter`. Never add it to a non-qualifying shift. All shift data (role, pay, time, distance, address) must come verbatim from the current turn's `get-marketplace-shifts` result, per the existing op-completed.md grounding rules, never fabricated for these templates.

Close every shift list with the standard CTA: "Reply 1, 2, or 3 to book, or tell me what matters most (distance, pay, or time) and I'll pull new options." (adjust the numbers named to however many shifts are shown, per op-completed.md).

## A. Offer Announcement (CKP)

Sent when a CKP offer is applied and the partner is already orientation-passed (trigger map §4). Pull shifts via `get-marketplace-shifts` and mark qualifying (Food Prep) shifts per the format above.

You've got a bonus offer: complete {required_count} Food Prep shifts within {window_days} days and earn ${bonus_amount} on top of your shift pay. I pulled some shifts near you. The Food Prep ones count toward your bonus:

[shift list, standard format above]

## B. Offer Announcement (DG)

Sent when a DG offer is applied and the partner is already orientation-passed.

You've got a bonus offer: complete {required_count} shifts within {window_days} days and earn ${bonus_amount} on top of your shift pay. I pulled some shifts near you. Qualifying ones count toward your bonus:

[shift list, standard format above]

## C. Progress Nudge (qualifying shift completed, offer not yet finished)

Sent after a qualifying shift completes and the partner has not finished the offer. Call `payment_bonuses_tool` for the exact `{completions}`/`{remaining}` before sending, don't assume the count just because a shift completed, another may have landed since.

Nice work on that shift, {first_name}! That's {completions} of {required_count} qualifying shifts completed toward your ${bonus_amount} bonus. {remaining} more to go by {expiry_date}. Want me to find your next shift?

## D. Progress Nudge, With Shift List (used when remaining is low, e.g. 1 left)

Include fresh shift options so the partner can act immediately.

You're almost there, {first_name}. {completions} of {required_count} qualifying shifts done, just {remaining} more to earn your ${bonus_amount} bonus by {expiry_date}. Here are some shifts near you:

[shift list, standard format above]

## E. Halfway Reminder (CKP ONLY, day 7 of 14, not completed)

CKP-only per spec §4, DG's 30-day window has no halfway trigger in this round. Only fires if `status: "active"` (partner has not completed the offer).

Hey {first_name}, you're halfway through your bonus window. You've completed {completions} of {required_count} qualifying shifts so far. Your ${bonus_amount} bonus expires on {expiry_date}, so you've got about a week left. Want me to find qualifying shifts you can pick up this week?

## F. Expiration Reminder (CKP, expiry minus 3 days / day 11 of 14, not completed)

Only fires if `status: "active"`.

Heads up, {first_name}. Your ${bonus_amount} bonus offer expires on {expiry_date}. You've completed {completions} of {required_count} qualifying shifts so far. Want me to find qualifying shifts you can pick up before then?

## G. Expiration Reminder (DG, expiry minus 3 days / day 27 of 30, not completed)

Same copy as Template F, DG's trigger just fires on day 27 instead of day 11 (engineering-owned timing, spec §4). Only fires if `status: "active"`.

Heads up, {first_name}. Your ${bonus_amount} bonus offer expires on {expiry_date}. You've completed {completions} of {required_count} qualifying shifts so far. Want me to find qualifying shifts you can pick up before then?

## H. Completion Confirmation (CKP or DG)

Sent once, on the final qualifying completion. `status` moves to `"completed"` after this, no further lifecycle templates apply to this offer.

Congratulations, {first_name}! You've completed all {required_count} qualifying shifts and earned your ${bonus_amount} bonus. It'll be credited to your account after your shifts are approved. Here are some more shifts near you if you want to keep going:

[shift list, standard format above, no "(Counts toward bonus)" marking needed since the offer is complete]

## Exit Conditions
- `status: "completed"` → send Template H once, then stop referencing the offer entirely (no further nudges).
- `status: "expired"` → stop referencing the offer, do not send Templates C/D/E/F/G after expiry.
- Unsubscribe → stop per HARD RULE 2/11 in `system-base.md`, unchanged.

## Do Not
- Send a progress nudge without a fresh `payment_bonuses_tool` call this turn
- Mark a non-qualifying shift "(Counts toward bonus)"
- Send the CKP halfway reminder (Template E) for a DG offer, DG has no halfway trigger this round
- Reference a previous or expired offer once a new one replaces it
- Send Template H more than once per offer
- Continue sending C/D/E/F/G after `status` is `"completed"` or `"expired"`
- Use an em dash anywhere in these templates
- Fabricate shift details for the shift list, pull them verbatim from the current turn's `get-marketplace-shifts` result
