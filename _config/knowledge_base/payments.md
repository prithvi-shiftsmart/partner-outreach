# Payments — Source of Truth

Built from the four Shiftsmart Help Center articles on Payout Methods + Stripe verification policy. Loaded into the prompt whenever the partner's message contains payment/bank/cashapp/itin/stripe/etc keywords.

## 1. Quick Reference: Supported vs Unsupported

| Supported | Unsupported |
|-----------|-------------|
| Bank account (direct deposit) | CashApp / Cash App card |
| Traditional debit card linked to a bank account | Apple Pay |
| | PayPal |
| | Zelle |
| | Paper checks |

## 2. Stripe Verification

Shiftsmart processes payments via **Stripe**. Verification requires:

1. **Full legal name** matching their **SSN or ITIN** (ITIN is accepted — confirmed by Help Center).
2. **Unexpired government ID**, one of:
   - Passport
   - Passport card
   - Driver's license
   - State-issued ID card
   - Resident permit / U.S. Green Card
   - Border crossing card
   - NYC card
   - Business EIN number (for business tax filings)

## 3. One Account Per Person

| Mapping | Constraint |
|---------|------------|
| Bank account | Can only link to **one Stripe Account** |
| Stripe Account | Can only link to **one Partner ID** |
| Shared payment methods (3+ profiles) | **Permanent removal** under ToS §4.1 |

The concierge should **never** suggest a partner use someone else's bank account or share methods. If a partner mentions doing this, redirect immediately.

## 4. Setup & Management Paths

### Adding a payout method
**Earnings tab** ($ icon at the bottom) → **Payment Accounts** → **"Add a bank or card"**

### Changing or removing a payout method
You must have **at least one default method** at all times. Add the new method **first**, then remove the old.

**To remove:**
1. Tap the **$ icon** on the home screen
2. Go to **Funds**
3. Scroll to **Payment Accounts** (at the bottom)
4. Tap the account you want to edit
5. Tap **Remove**

### Fixing payment account errors
**Delete and re-add** the account.

## 5. Payout Timing

- **Shiftsmart pays out same-day** after a shift completes.
- Stripe (the bank-side processor) takes **1–2 business days** to deposit it into the partner's bank account.
- Total time from shift completion to money in the partner's account = **1–2 business days**.

**Lead with same-day** when partners ask "when do I get paid?". Only surface the Stripe delay if the partner names "Stripe", asks why their deposit is delayed, or follows up that the money hasn't landed yet.

## 6. Orientation $10 Pay

- The $10 lands once the partner completes the **background check (step 4 of the In-app orientation)**.
- After it pays out, partners can confirm by tapping the **Earnings** tab at the bottom of the app.
- If they say "I did orientation but didn't get $10": confirm whether they finished step 4 (BGC submission). The $10 is gated on BGC submission, not on the learning modules.

## 7. Common Errors → Canonical Responses

| Error | Reply |
|-------|-------|
| "Not verified" | "Finish your Stripe verification — full legal name matching your SSN/ITIN, plus an unexpired government ID. Open the Earnings tab → Payment Accounts to check status." |
| "Invalid card" | "Double-check the card details (number, expiration, ZIP). If everything looks right, the card may not be supported — Shiftsmart needs a bank account or traditional debit card linked to a bank account." |
| "Declined by bank" | "That one's between you and your bank — give them a call to ask why the deposit is being declined, then try linking again." |
| "Funds stuck" / can't withdraw | "Don't try to withdraw again until your Stripe verification is fully complete. Once it is, submit a support ticket and the team can reset the payout for you." |
| "Wrong account" / paid to wrong place | "Submit a support ticket with the shift date, the amount, and the correct account details so the team can fix it." |

## 8. Do Not

- Suggest CashApp, Apple Pay, PayPal, Zelle, or checks as workarounds.
- Loop on unsupported-method explanations beyond ONE turn (then route to support).
- Suggest using someone else's account.
- Open a support ticket for unsupported-method questions.
- Lead with "1–2 business days" when partners ask when they get paid — lead with "same day".
- Mention the Stripe delay unless the partner asks specifically about it.

## 9. Escalate to Support When

All of the following are true:

- Stripe verification is complete
- Partner has waited at least 1–2 business days
- Error persists
- Partner can provide the **exact** error message

Do **not** suggest tickets for: questions about unsupported methods, setup questions answered by §4, or "when will my $10 land" before BGC is complete.
