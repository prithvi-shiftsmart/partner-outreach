# search_shifts

Queries available shifts near the partner, filtered by their preferences and sorted by the specified criteria.

## When to call
- On OP->S1A trigger: initial shift surfacing (top 3 by quality score)
- When partner states a preference (re-query with filter)
- When partner says "more" (offset by 3)
- During cancellation recovery (re-surface 3 fresh options)
- On inactivity nudge (refreshed top 3)

## Sort options
- `quality_score` (default): best overall match
- `distance_asc`: closest first
- `pay_desc`: highest pay + bonus first

## Important behaviors
- Always returns at most 3 shifts
- If no shifts match, returns empty array -- agent should say so honestly
- Shift data is the ONLY source of truth -- agent must never fabricate shift details
- Bonus field is 0 when no bonus is active -- agent should omit bonus text when 0
