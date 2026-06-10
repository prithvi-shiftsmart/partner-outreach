# Local → Production Path Mapping

Reference for porting local prompt edits to the monorepo. Production base path:
`applications/marketplace-api/src/`

Local paths now mirror production directory structure. The only difference is `.md` (local) vs `.prompt.ts` (production).

## Common (shared across both agents)

| Local | Production |
|-------|-----------|
| `common/concierge/system-base.md` | `common/concierge/system-base.prompt.ts` |
| `common/concierge/guardrails.md` | `common/concierge/guardrails.prompt.ts` |
| `common/concierge/tone-and-voice.md` | `common/concierge/tone-and-voice.prompt.ts` |
| `common/concierge/keyword-prefilter.json` | `common/concierge/keyword-prefilter.ts` |
| `common/concierge/knowledge-base/backup-floater-shifts.md` | `common/concierge/knowledge-base/backup-floater-shifts.prompt.ts` |
| `common/concierge/knowledge-base/getting-paid.md` | `common/concierge/knowledge-base/getting-paid.prompt.ts` |
| `common/concierge/knowledge-base/how-shifts-work.md` | `common/concierge/knowledge-base/how-shifts-work.prompt.ts` |
| `common/concierge/knowledge-base/orientation-process.md` | `common/concierge/knowledge-base/orientation-process.prompt.ts` |
| `common/concierge/knowledge-base/pay-rates.md` | `common/concierge/knowledge-base/pay-rates.prompt.ts` |
| `common/concierge/knowledge-base/payments.md` | `common/concierge/knowledge-base/payments.prompt.ts` |
| `common/concierge/knowledge-base/platform-policies.md` | `common/concierge/knowledge-base/platform-policies.prompt.ts` |
| `common/concierge/knowledge-base/ckp/ckp-orientation-walkthrough.md` | `common/concierge/knowledge-base/ckp/ckp-orientation-walkthrough.prompt.ts` |
| `common/concierge/knowledge-base/ckp/ckp-food-prep-guide.md` | `common/concierge/knowledge-base/ckp/ckp-food-prep-guide.prompt.ts` |
| `common/concierge/knowledge-base/dg/dg-orientation-walkthrough.md` | `common/concierge/knowledge-base/dg/dg-orientation-walkthrough.prompt.ts` |
| `common/concierge/knowledge-base/dg/dg-shift-guide.md` | `common/concierge/knowledge-base/dg/dg-shift-guide.prompt.ts` |

## New Download Agent (pre-OP)

| Local | Production |
|-------|-----------|
| `modules/concierge-new-download/prompts/funnel-stages/outreach.md` | `modules/concierge-new-download/llm/prompts/funnel-stages/outreach.prompt.ts` |
| `modules/concierge-new-download/prompts/funnel-stages/answering-qs.md` | `modules/concierge-new-download/llm/prompts/funnel-stages/answering-qs.prompt.ts` |
| `modules/concierge-new-download/prompts/funnel-stages/ready-to-orient.md` | `modules/concierge-new-download/llm/prompts/funnel-stages/ready-to-orient.prompt.ts` |
| `modules/concierge-new-download/prompts/funnel-stages/mid-orientation.md` | `modules/concierge-new-download/llm/prompts/funnel-stages/mid-orientation.prompt.ts` |
| `modules/concierge-new-download/prompts/funnel-stages/op-completed.md` | `modules/concierge-new-download/llm/prompts/funnel-stages/op-completed.prompt.ts` |
| `modules/concierge-new-download/prompts/funnel-stages/dormant.md` | `modules/concierge-new-download/llm/prompts/funnel-stages/dormant.prompt.ts` |
| `modules/concierge-new-download/prompts/response-playbook/*.md` | `modules/concierge-new-download/llm/prompts/response-playbook/*.prompt.ts` |
| `modules/concierge-new-download/prompts/message-templates/welcome-dl.md` | `modules/concierge-new-download/llm/prompts/message-templates/welcome-dl.prompt.ts` |
| `modules/concierge-new-download/prompts/message-templates/orientation-nudge.md` | `modules/concierge-new-download/llm/prompts/message-templates/orientation-nudge.prompt.ts` |
| `modules/concierge-new-download/prompts/message-templates/post-op-shift.md` | `modules/concierge-new-download/llm/prompts/message-templates/post-op-shift.prompt.ts` |
| `modules/concierge-new-download/prompts/message-templates/dormant-reengagement.md` | `modules/concierge-new-download/llm/prompts/message-templates/dormant-reengagement.prompt.ts` |

## Orientation Passed Agent (post-OP)

| Local | Production |
|-------|-----------|
| `modules/concierge-orientation-passed/prompts/funnel-stages/op-completed.md` | `modules/concierge-orientation-passed/llm/prompts/funnel-stages/op-completed.prompt.ts` |
| `modules/concierge-orientation-passed/services/partner-information.md` | `modules/concierge-orientation-passed/services/partner-information.ts` |
| `modules/concierge-orientation-passed/prompts/knowledge-base/*.md` | Local-only (not yet in production) |
| `modules/concierge-orientation-passed/prompts/message-templates/*.md` | Local-only (not yet in production) |

## Tools

| Local | Production |
|-------|-----------|
| `modules/assignment-tools/assign-shift.md` | `modules/assignment-tools/assignment-tools.constants.ts` |
| `modules/shift-tools/get-marketplace-shifts.md` | `modules/shift-tools/shift-tools.constants.ts` |

## Dispatch Router

| Local | Production |
|-------|-----------|
| `modules/concierge-dispatch/routing-rules.md` | `modules/concierge-dispatch/services/concierge-dispatch.service.ts` |

## Operational Configs (local only)

| Local | Notes |
|-------|-------|
| `_config/auto_responses.json` | Keyword auto-responses |
| `_config/campaigns.json` | Campaign definitions |
| `_config/markets.json` | Market scope |
| `_config/personalization_rules.md` | Partner matching |
| `_config/query_cache_rules.md` | BQ cache policy |
| `_config/query_registry.json` | Campaign-query registry |
| `_config/state_machine.json` | State transitions + agent assignments |
| `_config/timing_rules.md` | Cooldowns, rate limits |

## Porting Convention

Local uses `.md` files with prompt text. Production uses `.prompt.ts` files exporting template literal strings.

To port a local edit to production:
1. Edit the `.md` file locally
2. Test with replay fixtures
3. Copy the prompt text into the corresponding `.prompt.ts` export in the monorepo
4. The path mapping is now 1:1 — just swap `prompts/` for `llm/prompts/` and `.md` for `.prompt.ts`
