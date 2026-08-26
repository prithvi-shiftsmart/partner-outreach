# DxGy Bonus — Source of Truth

Covers Shiftsmart's DxGy ("Deal x Get y") completion bonus offers for CKP (Circle K Premium) and DG (Dollar General). Loaded whenever the partner's message contains bonus/offer keywords, or whenever an `## Active Bonus Offer` block is present in context. Both agents (`concierge-new-download` and `concierge-orientation-passed`) use this file.

Terms in this file are the general shape of DxGy offers. A specific partner's actual numbers ALWAYS come from the injected `## Active Bonus Offer` block (see `../dxgy-offer-context.md`) or a live `payment_bonuses_tool` call (see `../../../modules/payment-bonuses-tools/payment-bonuses-tool.md`), never from this file. If neither source is available for a partner, do not state numbers, guide them to the app instead.

## 1. Current Deal Shapes

| Deal | Required shifts | Window | Amount |
|---|---|---|---|
| CKP (Circle K) | 3 qualifying Food Prep shifts | 14 days | $75 |
| DG (Dollar General) | 3 qualifying shifts | 30 days | $50 |

Treat this table as the reference shape only. Always confirm the partner's specific `amount`, `required_count`, and `expiry_date` from their offer context before quoting numbers back to them, offers can vary by partner and market.

## 2. What Qualifies

- Only shifts matching the offer's `qualifying_filter` (company + role, e.g. Circle K Food Prep shifts) count toward the required count.
- The In-app orientation does NOT count as a qualifying shift, it is a separate, one-time {{orientation_payout}} payment.
- Non-qualifying roles at the same company do not count, even if the partner works them.
- When surfacing shifts to a partner with an active offer, mark ONLY the shifts matching `qualifying_filter` with "(Counts toward bonus)". Never mark a non-qualifying shift this way.

## 3. Payout Timing

- The bonus is paid **on top of shift pay**, it is a separate credit, not baked into the hourly rate.
- It is credited to the partner's account **after their qualifying shifts are approved**.
- This typically happens within a few days of completion. Never promise a specific date, and never say the bonus pays instantly.
- NEVER guarantee an exact timing beyond "a few days after your shifts are approved."

## 4. Deadline Behavior

- Offers expire on a fixed `expiry_date`. There are no extensions.
- If the partner does not complete the required count by `expiry_date`, the offer expires, and shifts completed after that date do not earn the bonus.
- Partners cannot request a different deadline. See the Decline Patterns section below.

## 5. Offer Replacement

- A partner has at most one active offer at a time.
- If a new offer is applied while a previous one is still open, the new offer replaces it. Only the current offer's terms may be stated; never restate a previous or expired offer's terms or amount. Acknowledging the replacement itself is fine.
- If the partner asks about an offer that has already expired, acknowledge it has ended (without restating its terms), make clear new shifts will not count toward it, and pivot to normal shift discovery.

## 6. Budget Cap

- A market-level budget cap stops NEW offer applications once reached.
- It does NOT revoke or shorten an offer a partner already has. Partners with an existing active offer keep it on its original terms through expiry or completion, regardless of the cap.

## 7. Common Questions → Canonical Responses

| Question | Canonical response pattern |
|---|---|
| "What do I need to do?" | "You need to complete {required_count} qualifying shifts by {expiry_date} to earn ${amount}. You've done {completions} so far." |
| "Which shifts count?" | "Any {qualifying description} shifts count toward your bonus. Want me to find some near you?" |
| "How much is the bonus?" | "Your current offer is ${amount} for completing {required_count} shifts by {expiry_date}." |
| "When is the deadline?" | "Your offer expires on {expiry_date}. You've completed {completions} of {required_count} so far." |
| "How close am I?" | Call `payment_bonuses_tool` first, then: "You've completed {completions} of {required_count} qualifying shifts. {remaining} more to go by {expiry_date}!" |
| "When do I get paid?" | "Your bonus will be credited to your account after your qualifying shifts are approved. This typically happens within a few days of completion." |
| "I completed all my shifts but haven't been paid" | "Bonus payments are credited after your shifts are approved, which can take a day or two. If it's been longer than that, reach out to the support team through the app. Tap the message icon in the top right corner, then tap 'Send us a message' to start a new chat." |

Fill `{amount}`, `{required_count}`, `{completions}`, `{remaining}`, `{expiry_date}`, and the qualifying description ONLY from the injected offer context or a live `payment_bonuses_tool` result. Never invent a number.

## 8. Decline Patterns (No Support Routing)

These are polite no's, not escalations. Do NOT route either to support:

- "Can I get a different offer?" → "This offer is tied to your account, I'm not able to change or swap it. This one's worth ${amount} for {required_count} shifts, happy to help you find qualifying shifts if you want to work toward it."
- "Can I extend my deadline?" → "Deadlines are fixed once an offer is issued, I can't extend them. You've got until {expiry_date} on this one, want me to find shifts you can pick up before then?"

## 9. Escalation Matrix (Support Routing Required)

Route to human support via in-app chat (tap the message icon, top right corner, then "Send us a message" to start a new chat) for:

- "My bonus didn't show up" / "I completed my shifts but wasn't paid" (after the day-or-two approval window has passed)
- Any dispute about the bonus amount, count, or whether a specific shift qualified
- Any claim that the offer terms shown don't match what the partner was told elsewhere

Never guess at or resolve a payment dispute yourself, terms and payment status come only from the offer context / tool, disputes go to a human.

## Do Not

- State any amount, count, or deadline not present in the injected offer context or a `payment_bonuses_tool` result
- Reference a bonus at all when no active offer exists (`## Active Bonus Offer` absent / `has_active_offer: false`)
- State the terms or amount of a previous or expired offer once a replacement is in effect or the window has closed
- Promise instant payment or a specific payout date
- Mark a non-qualifying shift "(Counts toward bonus)"
- Offer to change, swap, or extend a bonus offer
- Route "different offer" or "extend deadline" requests to support, those are declines, not escalations
- Loop on a payment dispute, one acknowledgement then escalate
