# Trigger -- OP -> S1A

## When this fires
Partner reaches OP status (in-app orientation complete, BGC submitted) in a market with the OP->S1A flag enabled.

## Context available at trigger time
- Partner identity: name, phone, partner_id
- Partner location: lat/lng for distance ranking
- Funnel state: must equal OP (verified via get_partner_profile)
- Top 3 shifts near partner (pre-fetched via search_shifts)

## Opening message structure
1. Congratulate on finishing orientation (one line)
2. Present 3 shifts using shift card format
3. Booking CTA: "Reply 1, 2, or 3 to book"
4. App mention: "You can also browse all open shifts in the app anytime"
5. Preference fallback: "let me know what matters most -- distance, pay, or time"

## If no shifts available at trigger time
- Say so honestly: "I checked for shifts near you but nothing's open right now"
- Commit to checking back: "I'll check back tomorrow when new shifts post"
