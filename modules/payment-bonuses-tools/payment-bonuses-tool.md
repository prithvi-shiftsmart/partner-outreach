# Tool: payment_bonuses_tool

**Prod file:** `modules/payment-bonuses-tools/payment-bonuses-tools.constants.ts` (schema/description) + `payment-bonuses-tools.service.ts` (handler) — NEW module, does not exist in prod yet. Mirrors the `shift-tools` / `assignment-tools` convention (see `../shift-tools/get-marketplace-shifts.md`, `../assignment-tools/assign-shift.md`).
**Tool name:** `payment_bonuses_tool`
**Owner:** EPD

Tool name locked 2026-07-28 (`48 - DxGy Prompt Update Spec.md` decision #1). The PRD's `get_bonus_status` references are stale aliases of this tool, treat any PRD mention of `get_bonus_status` as `payment_bonuses_tool`.

## Purpose

Returns the authoritative live state of a partner's DxGy bonus offer: whether one is active, its terms, and progress toward completion. This is the only source of truth for progress (`completions` / `remaining`), the injected `## Active Bonus Offer` block (see `../../common/concierge/dxgy-offer-context.md`) covers terms but can go stale between turns.

## When to Use

CALL THIS TOOL — DO NOT GUESS OR CACHE — in each of these situations:
- Every time the partner asks a DxGy bonus question (terms, progress, deadline, payout timing)
- Before sending any progress nudge (announcement, "X of Y done", halfway, expiration, completion)
- Before confirming or correcting a partner's claim about their own progress
- Any time the injected `## Active Bonus Offer` block might be stale (e.g. the partner just mentioned completing a shift)

Never assume progress carried over from earlier in the conversation. Never answer a progress question from memory, always call the tool.

## Input Schema

| Field | Type | Required | Description |
|---|---|---|---|
| `partner_id` | string (UUID) | TBD, see Open Flag below | Partner to look up |

## Open Flag for Eng — `partner_id` Param

The prod tool convention already shipped for this repo's other tools (`get-marketplace-shifts`, `assign_shift`) scopes the partner implicitly via request/auth context and takes **no** `partner_id` parameter. Expect the shipped `payment_bonuses_tool` schema to follow that same convention and drop `partner_id`. This doc documents both shapes until eng confirms the final schema (spec §6, open flag #2):

- **If context-scoped (expected):** call with no arguments, or an empty object, the partner is resolved server-side the same way it is for the other two tools.
- **If `partner_id` is required:** pass the partner_id from context, never invent one or ask the partner for their own ID.

## Output / Artifact

| Field | Type | Description |
|---|---|---|
| `has_active_offer` | boolean | `false` means the partner has no active offer. When false, no other field should be used, and the word "bonus" must not appear in the reply |
| `bonus_id` | string (UUID) | Offer identifier |
| `type` | string | `"completion"` |
| `amount` | number | Dollar bonus amount |
| `required_count` | number | Qualifying shifts needed |
| `completions` | number | Qualifying shifts completed so far |
| `remaining` | number | `required_count - completions` |
| `qualifying_filter` | object | Company/role (or other) filter defining what counts, render as a human description, never raw JSON |
| `start_date` | string (ISO date) | Offer start |
| `expiry_date` | string (ISO date) | Offer deadline |
| `status` | string | `"active"` \| `"completed"` \| `"expired"` |
| `deep_link` | string | App deep link to the offer detail screen |

## Usage Rules

- Call on every DxGy question, terms or progress. Don't answer a progress question from the injected context block alone, it can be stale.
- Call before any progress nudge, every time. Never send a lifecycle template (`dxgy-progress.md`) off a cached or assumed count.
- Never cache the result across turns. A fresh call is required each time progress matters.
- `has_active_offer: false` → the agent must never reference any bonus, amount, or offer to the partner. Fall back to normal shift-discovery behavior with no bonus framing.
- `status: "expired"` or `"completed"` → do not send further progress nudges. `"completed"` triggers exactly one completion confirmation, then stop.

## Access Control

- Read-only, does not modify offer or assignment state.
- Available to BOTH agents, `concierge-new-download` (pre-OP) and `concierge-orientation-passed` (post-OP), per spec decision #4. This is a departure from the prior convention that the new-download agent has no tool access at all (only `op_completed` had tools), DxGy is the first tool the DL agent gets.

## Notes

- Pairs with the injected `## Active Bonus Offer` block for terms, this tool for live progress. See `../../common/concierge/dxgy-offer-context.md`.
- `qualifying_filter` is the same shape referenced by the shift-card marking rule in `op-completed.md` ("(Counts toward bonus)"), scope shift-list marking to whatever this tool (or the offer context block) returns, never invent a qualifying rule.
