# Tool: get-marketplace-shifts

**Prod file:** `modules/shift-tools/shift-tools.constants.ts` (schema/description) + `shift-tools.service.ts` (handler) + `shift-tools.types.ts` (artifact types)
**Tool name:** `get-marketplace-shifts`
**Owner:** EPD (Eton)

Local previously documented this as `retrieve_quality_shifts` with a `quality_score` sort and a `partner_id` input parameter. That tool does not exist in prod. This file replaces it with the actual `get-marketplace-shifts` tool.

## Purpose

Returns shifts available to the current partner, scoped to today and the future. The partner's home location is the default search center — omit latitude/longitude unless the partner gave a different one. Called by the `op_completed` state (see [`../concierge-orientation-passed/prompts/funnel-stages/op-completed.md`](../concierge-orientation-passed/prompts/funnel-stages/op-completed.md)); no other state has tool access.

## When to Use

CALL THIS TOOL — DO NOT GUESS — every time shift data is needed, including whenever the partner asks for different shifts than the ones last shown. Examples that require a fresh call:
- "show me ones that pay more" → call again with `shiftQueryType=ALL` and `sort=PAY`
- "anything closer?" → `sort=DISTANCE`
- "what about tomorrow?" → `selectedDay=1`
- "any morning shifts?" → keep last sort, narrow to a day window and filter client-side in the response
- A previously offered shift was taken between display and assignment → re-query with the same args used last time

## Input Schema (Zod-validated, `.strict()`)

There is **no `partner_id` parameter.** The partner is scoped implicitly via request context/auth — never pass a partner identifier.

| Field | Type | Required | Description |
|-------|------|----------|--------------|
| `filters.addressRef` | string | no | Site/address UUID to filter by |
| `filters.companyIds` | string[] | no | Restrict to shifts belonging to these company UUIDs |
| `filters.roleIds` | string[] | no | Restrict to shifts requiring one of these role UUIDs |
| `filters.shiftTypes` | string[] | no | Restrict to shifts of these types (e.g. `"FIXED"`, `"FLEX"`) |
| `latitude` | number | no | Search latitude. Omit to use the partner's home location on file. |
| `longitude` | number | no | Search longitude. Omit to use the partner's home location on file. |
| `maxDistance` | number | no | Search radius in miles. Defaults to 30 when omitted. |
| `limit` | int | no | Page size. Omit to use the upstream default; pass 3-5 for SMS surfacing. |
| `page` | int | no | 1-indexed page number |
| `selectedDay` | int | no | Days offset from today in the partner's timezone (0 = today, 1 = tomorrow). Omit for any future day. |
| `shiftQueryType` | enum | no | See buckets below. Defaults to `ALL` when omitted. |
| `sort` | enum | no | See sort options below. Required when the partner expresses a preference (distance/pay/start) so the top of the list reflects their ask. |

`filters` is its own `.strict()` object — `companyIds`/`roleIds` are the mechanism for scoping to the tuples in the injected `## Partner Information` block (see [`../concierge-orientation-passed/services/partner-information.md`](../concierge-orientation-passed/services/partner-information.md)); never invent UUIDs.

### `shiftQueryType` buckets

| Value | Meaning |
|-------|---------|
| `ALL` | Default for general discovery. Pulls every shift the partner is eligible for (orientation, dispatch, locked, recently cancelled), already future-only. Use for the first lookup and any preference re-query. |
| `RECOMMENDED_SHIFTS` | The algorithm's ranked picks; use when the partner asks for "best" or expresses no preference. |
| `LOCKED_SHIFTS` | Only shifts the partner cannot grab without unlocking; rarely surfaced directly. |
| `ORIENTATION` / `ORIENTATION_RECOMMENDED` / `ORIENTATION_UNLOCK_SHIFTS` | Orientation-linked buckets; niche, only on explicit ask. |
| `DISPATCH` | Niche; only on explicit ask. |
| `REFERRAL` | Niche; only on explicit ask. |
| `SURVEY` | Niche; only on explicit ask. |
| `STORE_UPCOMING` | Niche; only on explicit ask. |

### `sort` options (`SHIFT_SORT_OPTIONS`, only meaningful for `ALL` / `RECOMMENDED_SHIFTS`)

| Value | Meaning |
|-------|---------|
| `ALGORITHM` | Quality-score ranking; use when the partner has no preference (this is prod's replacement for local's old `quality_score` sort concept). |
| `DEFAULT` | Leaves ordering to the upstream service. |
| `DISTANCE` | Closest first; "closest" / "near me". |
| `PAY` | Highest pay first; "highest pay", "more money", "best paying". |
| `START` | Soonest start first; "today", "as soon as possible". |

## No client-side time-of-day or date-range filter

The tool has `selectedDay` (single day, 0-indexed from today) but nothing else for date/time narrowing. "Morning shifts," "this week," and similar asks are filtered by the model client-side after calling the tool with a broader query — see the "Filtering Without Tool Support" section of [`op-completed.md`](../concierge-orientation-passed/prompts/funnel-stages/op-completed.md).

## Output / Artifact

The tool result carries a structured artifact (`GetMarketplaceShiftsToolArtifact` in `shift-tools.types.ts`), not just tool-message text:

```ts
type GetMarketplaceShiftsToolArtifact =
  | { status: 'failure'; error: string }
  | {
      status: 'success';
      offeredShifts: readonly ShiftForLlm[]; // top-N enriched shifts in render order
      partnerTimezone: string;
      result: MarketplaceShiftsResult;       // raw upstream result
    };
```

`offeredShifts` is the render-order list the LLM was shown as cards — downstream consumers (booking confirmation, server-side re-render) index into it by `uuid` without re-running enrichment. Each shift includes a `uuid` (`id=<uuid>` in the rendered text) that `assign_shift` requires — see [`../assignment-tools/assign-shift.md`](../assignment-tools/assign-shift.md).

## Access Control

- Read-only — does not modify shift or assignment state.
- Available only in the `op_completed` state.

## Notes

- Scope `companyIds`/`roleIds` from `## Partner Information`; never invent UUIDs.
- Returned shift uuids become the authoritative `Previous Shift Offer` list the `assign_shift` structural guard validates against — see [`../assignment-tools/assign-shift.md`](../assignment-tools/assign-shift.md).
- There is no `quality_score` field in the output; ranking is controlled entirely via `sort` at query time.
