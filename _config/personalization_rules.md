# Personalization Rules

## Work Experience Mapping
When onboarding data includes prior work experience:
- Retail (Walmart, Target, etc.) -> recommend PepsiCo shifts first
- Food service -> recommend Circle K Premium first
- Warehouse/logistics -> recommend PepsiCo or Dollar General
- No prior relevant experience -> simplest shift type, closest location

## Company Display Names
- "Circle K - Premium" -> "Circle K"
- "PepsiCo Beverages" -> "PepsiCo"
- "PepsiCo Foods" -> "Frito-Lay"
- "Dollar General" -> "Dollar General"

## Deduplication
- A partner should not receive messages from more than one campaign per day
- Priority order: incomplete_orientation > activation > referral

## Cooldown
- Don't message a partner if they were messaged in the last 48 hours
- Check: `SELECT 1 FROM message_log WHERE partner_id = ? AND logged_at > datetime('now', '-48 hours')`

## Shift Count Progression
- 0 shifts: simple, close shifts only. Max 3 options.
- 1-4 shifts: moderate variety. Include pay comparisons.
- 5+ shifts: full catalog. Surface higher-paying shifts.
