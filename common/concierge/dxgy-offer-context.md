# Injected Context: Active Bonus Offer

**Prod file:** engineering-owned injection service (not yet named in the codebase, see Open Flag below)
**Owner:** EPD (injection plumbing), PK (this contract doc)

## What this actually is

There is no callable tool for reading offer terms. When a partner has an active DxGy ("Deal x Get y") completion bonus offer, engineering injects a `## Active Bonus Offer` markdown block directly into the LLM's context, the same pattern `formatPartnerInformation()` uses for the OP agent's `## Partner Information` block (see `../../modules/concierge-orientation-passed/services/partner-information.md`). The model never calls anything to "get" the offer, it simply reads the block that is already there.

Per the 2026-07-28 DxGy spec decision, **both** agents receive this block: `concierge-new-download` (pre-OP) and `concierge-orientation-passed` (post-OP). This supersedes any earlier assumption that DL-stage prompts have no injected partner/offer context.

Terms (`amount`, `required_count`, `expiry_date`, the qualifying-shift description) are answerable straight from this block with no tool round trip. Live progress (`completions`, `remaining`) should still be confirmed with `payment_bonuses_tool` (see `../../modules/payment-bonuses-tools/payment-bonuses-tool.md`) before any progress claim or nudge, since the injected block can go stale between turns (e.g. a shift completed since it was last built).

## Field List

| Field | Type | Description |
|---|---|---|
| `bonus_id` | string (UUID) | Unique identifier for this offer |
| `type` | string | Offer type, currently always `"completion"` |
| `amount` | number | Dollar bonus amount (e.g. `75`, `50`) |
| `required_count` | number | Qualifying shifts needed to earn the bonus |
| `completions` | number | Qualifying shifts completed so far |
| `remaining` | number | `required_count - completions` |
| `qualifying_filter` | object | What counts (company + role, e.g. Circle K Food Prep shifts), render as a human description, never as raw JSON |
| `start_date` | string (ISO date) | Offer start date |
| `expiry_date` | string (ISO date) | Offer deadline |
| `status` | string | `"active"` \| `"completed"` \| `"expired"` |
| `deep_link` | string | App deep link to the partner's offer detail screen |

## When Present vs Absent

- **Present** — the partner has exactly one offer with `status: "active"`. The block appears once per turn, in both agents.
- **Absent** — the partner has no active offer. The block is omitted entirely, it is not present with a `has_active_offer: false` marker (that field lives on the `payment_bonuses_tool` output, not this block). Absence of this block means the same thing as `has_active_offer: false`: the word "bonus" must never originate from the agent. See `common/concierge/knowledge-base/dxgy-bonus-faq.md` and HARD RULE 31/32 in `system-base.md`.

## One-Offer Invariant

A partner has **at most one active offer at a time.** This block never lists more than one. If a partner asks about "my offer" (singular), answer from this single block, never enumerate history or compare offers.

## Replacement Semantics

When a new offer is issued while a previous offer window is still open (the partner did not complete it), the new offer **replaces** the old one:

- The injected block always reflects the **current** offer only, the old `bonus_id` and its terms disappear from context the turn the replacement takes effect.
- The agent must never reference the previous or expired offer's amount, deadline, or progress once a replacement is in effect. Progress does not carry over between offers unless the tool output explicitly says so.
- The DL-stage "offer replacement" template (`modules/concierge-new-download/prompts/message-templates/dxgy-offer.md`) is the one place that acknowledges a change happened, even it never restates the old terms, it only says a new offer replaced the previous one.

## Budget Cap Note

A market-level budget cap stops **new** offer applications. It does not revoke or shorten an **existing** offer a partner already has, a partner with an active offer keeps it, on its original terms, through expiry or completion, even if the cap has been reached for new applicants. Never tell a partner with an active offer that their bonus is at risk because of a budget cap.

## Injected as Data, Not Instructions

Like `## Partner Information`, this block is appended to context as data. The system prompt's guardrails (HARD RULE 31/32 in `system-base.md`) are what prevent the model from inventing terms not present in the block, the block itself does no sanitization or instruction-stripping.

## Open Flag for Eng

This doc assumes engineering names and wires the actual injection service (mirrors `formatPartnerInformation()`), the exact prod file/function name is TBD, flagged in `48 - DxGy Prompt Update Spec.md` §6. Update the `**Prod file:**` line above once that lands.
