# Conversation Rules -- OP -> S1A

## SMS constraints
- Plain text only -- no markdown rendering in SMS
- Target under 320 characters per message (3 SMS segments max for shift cards)
- Middle dot (.) as inline separator
- Em dash (--) between role + sub-type, en dash (-) in time ranges

## Shift card format
Each shift on 3 lines:
- Line 1: `{number}. {Role} -- {Sub-type} . ${pay}` (append ` + ${bonus} bonus` if eligible)
- Line 2: `{Day} {M/D} . {start}-{end} . {distance}mi`
- Line 3: `{Brand}, {full street address}`

## Formatting rules
- Day format: abbreviated weekday + M/D (Tue 5/13)
- Distance: one decimal + mi (6.2 mi)
- Bonus: append ` + $X.XX bonus` after base pay; omit entirely if zero
- Full street address on its own line -- auto-links to Maps in SMS

## Response structure
- Answer the question / take the action first
- Then redirect to booking CTA if appropriate
- Don't repeat information the partner already has
