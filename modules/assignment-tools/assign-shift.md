# Tool: assign_shift

**Prod file:** `modules/assignment-tools/assignment-tools.constants.ts` (schema/description) + `assignment-tools.service.ts` (handler, structural guards) + `assignment-tools.types.ts` (artifact types)
**Tool name:** `assign_shift`
**Owner:** EPD (Eton)

Local previously documented this as `make_shift_assignment` with a `partner_id` + `shift_id` + `confirmation_required` boolean input. That tool does not exist in prod. This file replaces it with the actual `assign_shift` tool.

## Purpose

Assigns the partner to a shift via the SSM API. Called by the `op_completed` state (see [`../concierge-orientation-passed/prompts/funnel-stages/op-completed.md`](../concierge-orientation-passed/prompts/funnel-stages/op-completed.md)) as soon as the partner confirms a specific shift — a numeric reply IS the confirmation; there is no separate confirm-then-book round trip.

The handler resolves internally whether a **new assignment must be created** or an **existing pending/sent invite must be flipped to Accepted** (`ASSIGN_SHIFT_TOOL_TYPES.CREATE_NEW` vs `ACCEPT_EXISTING`) — the model never specifies or guesses which; it just passes the shift the partner confirmed.

## Input Schema (Zod-validated, `.strict()`)

There is **no `partner_id` parameter and no `confirmation_required` flag.** The partner is identified by runtime/auth metadata. Confirmation is enforced structurally (see Guards below), not by a boolean the model sets.

| Field | Type | Required | Description |
|-------|------|----------|--------------|
| `companyId` | string (UUID) | yes | Company UUID that owns the shift (e.g. the Circle K Premium uuid) |
| `shiftId` | string (UUID) | yes | Shift UUID the partner has confirmed they want |
| `selectedIndex` | int, 1-3 | yes | The 1-based position of the shift in the persisted **Previous Shift Offer** (1 = first, 2 = second, 3 = third). MUST exactly match the literal digit the partner typed. |
| `bonusAmount` | number | no | Optional dollar bonus to attach to the assignment. Omit if no incentive should be added. |

`companyId` and `shiftId` are validated as real UUIDs (`isUuid` refine) — malformed values are rejected before the handler runs.

## Structural Guards (enforced in `assignment-tools.service.ts`, not the prompt)

These run in order and each one independently rejects the call with a distinct error message (returned to the model as tool-error text, not a silent no-op):

1. **Numeric-pick requirement.** The partner's last message must contain a literal `1`, `2`, or `3` digit. Affirmatives ("yes", "book it", "sure") and descriptor picks ("the early one", "the first one") never satisfy this, even when only one shift was offered. Rejection message: *"the partner's last message did not contain a literal '1', '2', or '3'."*
2. **selectedIndex range.** Must be 1, 2, or 3. Rejection: *"selectedIndex must be 1, 2, or 3."*
3. **selectedIndex matches the partner's digit.** `selectedIndex` must equal the literal digit found in guard 1. Rejection: *"selectedIndex does not match any 1/2/3 digit in partner last message."*
4. **selectedIndex within the offer's length.** Rejected if `selectedIndex` exceeds how many shifts were actually in the persisted `Previous Shift Offer`. Rejection: *"selectedIndex is greater than the number of shifts in the previous offer."*
5. **shiftId ↔ selectedIndex cross-validation.** `lastOfferedShiftIds[selectedIndex - 1]` must equal the passed `shiftId`. This closes both the "uuid outside the offer" gap and the "digit doesn't match the chosen uuid" gap. Rejection: *"shiftId does not match the selectedIndex position."*

`lastOfferedShiftIds` here is the array persisted from the **prior turn's** `get-marketplace-shifts` call — never the same turn's. See the "no same-turn list → assign chaining" guard documented in [`op-completed.md`](../concierge-orientation-passed/prompts/funnel-stages/op-completed.md#agentic-loop--structural-guards).

Two additional server-side overrides (in `llm.service.ts`, applied after the tool call, not part of the tool itself) back these guards up:
- A successful `assign_shift` always gets its confirmation SMS rendered server-side from the booked shift's enriched data — never from the model's own generated text.
- A failed `assign_shift` is checked for a hallucinated `"you're booked"`-style reply from the model and, if found, forcibly overridden with the canonical failure-recovery copy.

## Output / Artifact

```ts
type AssignShiftToolArtifact =
  | { status: 'failure'; error: string }
  | { status: 'success'; result: AssignmentResult };
```

`AssignmentResult.kind` distinguishes `created` / `accepted` (success) from `failed` (a real SSM-side failure, distinct from a guard rejection — guard rejections never reach SSM at all and surface as `status: 'failure'`).

## Access Control

- **Write action** — modifies shift/assignment state.
- Available only in the `op_completed` state.
- Eligibility (orientation complete, not banned, etc.) is enforced upstream of this tool by the dispatch/eligibility layer — see [`../concierge-dispatch/routing-rules.md`](../concierge-dispatch/routing-rules.md) — not re-checked here.

## Notes

- There is no confirmation-mode/confirmed two-call handshake like the old local design (`confirmation_required: true` then `false`). Confirmation is the partner's literal digit in their prior message, checked structurally before the tool ever runs.
- Race condition (shift filled between offer and booking) surfaces as a `failed` result, not a guard rejection — the prompt's failure-recovery branch (re-query, show 3 fresh options) handles it.
- `EXISTING_ASSIGNMENT_LOOKUP_LIMIT = 25` bounds how many existing pending/sent assignments the handler scans when deciding create-vs-accept; not something the model needs to reason about.
