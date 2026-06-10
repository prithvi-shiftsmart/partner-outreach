# Concierge Router — Routing Rules

Maps to: `src/modules/concierge-router/services/concierge-router.service.ts`

## Routing Decision (on every inbound SMS)

```
Inbound SMS arrives
  │
  ▼
Is partner-concierge enabled? (LD flag)
  │── No → drop (no concierge response)
  │
  ▼
Is orientationPassed.enabled? (LD kill-switch)
  │── No → route to new_download agent
  │
  ▼
Check partner lifecycle via PartnerLifecycleService
  │
  ▼
Has partner completed orientation for ANY LD-enabled (companyId, projectId, roleId) tuple?
  │── No → route to new_download agent
  │
  ▼
Optional: geo gate (h3Geohashes + h3Rings on orientationPassed config)
  │── Outside zone → route to new_download agent
  │
  ▼
Route to orientation_passed agent
```

## First Crossover (new_download → orientation_passed)

When a partner is routed to `orientation_passed` for the first time:
1. Create a new `orientation_passed` conversation document (idempotent via partial unique index)
2. Close the existing `new_download` conversation document (status → `CLOSED`)
3. Subsequent inbound messages find the existing `orientation_passed` doc — no duplicate creates

This maps to `findOrCreateOrientationPassed` in the repository layer, which handles E11000 duplicate-key races by re-fetching the winning doc.

## OP-Completed Eligibility

Maps to: `src/modules/concierge-router/services/op-completed-eligibility.ts`

A partner is eligible for the orientation-passed agent when:
- Their lifecycle states include at least one state that is `OP` (orientation passed) or higher
- That state's `(companyId, projectId, roleId)` tuple appears in `opCompletedEnabledProjects` (LD config)

Helper functions:
- `isOpOrHigher(state)` — returns true if the lifecycle state ordinal is >= OP
- `findEnabledOpStates(lifecycleStates, enabledProjects)` — filters to only OP+ states that match the enabled project list

## LaunchDarkly Config Shape

```json
{
  "enabled": true,
  "orientationPassed": {
    "enabled": true,
    "h3Geohashes": [],
    "h3Rings": 5,
    "opCompletedEnabledProjects": [
      { "companyId": "...", "projectId": "...", "roleId": "..." }
    ]
  }
}
```

- `orientationPassed.enabled: false` → kill-switch, all partners go to new_download
- `opCompletedEnabledProjects: []` → no partners are eligible for orientation-passed
- `h3Geohashes: []` → geo gate disabled (all locations eligible)
