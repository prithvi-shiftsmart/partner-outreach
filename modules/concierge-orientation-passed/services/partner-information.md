# Service: formatPartnerInformation

**Prod file:** `modules/concierge-orientation-passed/services/partner-information.ts`
**Owner:** EPD (Eton)

## What this actually is

There is **no `retrieve_partner_info` callable tool.** Partner context is not something the model requests mid-conversation — it is a pure formatting function, `formatPartnerInformation()`, that the `op_completed` state (see [`../prompts/funnel-stages/op-completed.md`](../prompts/funnel-stages/op-completed.md)) calls once per turn to build a `## Partner Information` markdown block, which is injected directly into the LLM's context alongside the system prompt. The model never calls anything to "get" this data; it simply reads the block that's already there.

## Signature

```ts
function formatPartnerInformation(params: {
  enabledOpStates: readonly PartnerLifecycleState[];
  now: Date;
  partnerTimezone: string | undefined;
}): string
```

- `enabledOpStates` — the partner's lifecycle entries that are orientation-passed-or-later AND match an LD-enabled `(companyId, projectId, roleId)` tuple. Computed upstream by `findEnabledOpStates()` in [`../../concierge-dispatch/routing-rules.md`](../../concierge-dispatch/routing-rules.md) and passed down as `enabledOpStates` on every `handleInboundMessage` call.
- `now` — current timestamp, used to render the date/timezone anchor.
- `partnerTimezone` — partner's IANA timezone if known; falls back to `America/New_York` (`DEFAULT_TIMEZONE`) when absent.

## Output shape

Always returns a non-empty block — even with zero `enabledOpStates` — so the date/timezone anchor is always present and the model never has to infer "today's date" from the message body.

**With no enabled OP states:**
```
## Partner Information
Today is Tuesday, July 28, 2026 (2026-07-28) in the partner's timezone (America/New_York). When the partner says 'today' or 'tomorrow', resolve against this date — not against any date you may have seen in a previous reply.
```

**With one or more enabled OP states:**
```
## Partner Information
Today is Tuesday, July 28, 2026 (2026-07-28) in the partner's timezone (America/New_York). When the partner says 'today' or 'tomorrow', resolve against this date — not against any date you may have seen in a previous reply.

The partner has completed orientation for the following company/project/role combinations:
  - companyId: <uuid> | projectId: <uuid> | roleId: <uuid> | stage: op_completed

When calling get-marketplace-shifts or assign_shift, use the companyIds and roleIds from this block. Do not invent or substitute values.
```

Each row is one `enabledOpStates` entry: `companyId | projectId | roleId | stage`, straight off the partner's lifecycle state — not a fixed/curated profile object.

## What it deliberately does NOT include

No `partner_id`/`phone`/`zone_description`/`closest_store_miles`/`preferences`/`account_state`/`funnel_status` object, and no `first_name`/`last_name` — those concerns are handled elsewhere (message-window context, the partner-lifecycle service, and the shift tools' own location resolution). This block's only job is: anchor "today," and enumerate the companyId/projectId/roleId/stage tuples the model is allowed to scope tool calls to.

## Injected as data, not instructions

The block is appended to context as data. The system prompt's guardrails are what prevent the model from treating its contents as directives — `formatPartnerInformation` itself does no sanitization or instruction-stripping; it is a straight formatter.

## Access pattern

- Read-only, computed fresh every turn (not cached/stored on the conversation doc).
- Available only in `op_completed` — the only state with tool access. Earlier funnel-stages (new-download agent) never see this block.

## Why this replaces the old `retrieve_partner_info` tool design

Local previously documented this as a callable JSON-schema tool (`retrieve_partner_info(partner_id, fields[])` → `{profile, funnel_status, preferences, account_state}`) that the model would invoke to "verify OP completion" or "get location for shift query." That tool never shipped. In production, OP-completion is established once, upstream, by the dispatch/eligibility layer before the orientation-passed agent is ever invoked (`ConciergeDispatchService` + `OpEligibilityService` + `findEnabledOpStates`) — by the time `op_completed` runs, eligibility is already resolved, and the only per-turn need is the companyId/projectId/roleId scoping plus a stable "today" anchor, which is exactly what `formatPartnerInformation()` provides. Location for shift queries comes from the partner's home location on file (used implicitly by `get-marketplace-shifts` unless lat/long are passed) — not from this block.
