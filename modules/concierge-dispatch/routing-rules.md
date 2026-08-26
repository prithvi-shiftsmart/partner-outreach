# Concierge Dispatch — Routing Rules

Maps to: `src/modules/concierge-dispatch/services/concierge-dispatch.service.ts` (`ConciergeDispatchService`)

There is no `concierge-router` module in prod — the module is `concierge-dispatch`. Local previously mis-named it; corrected throughout this file.

> **Production also has `concierge-dispatch-graph` (as of Aug 2026), not yet mirrored locally** — a LangGraph `StateGraph` dispatch with a deterministic router node (`state.orientationPassed` → `shift_booking`, else `onboarding`; plus a `support` route), checkpointer-backed state, and BullMQ inbound/shadow/wake queues. This file documents the legacy `ConciergeDispatchService`, which still coexists on main. See `mapping.md` for the follow-up.

`ConciergeDispatchService` receives a preloaded `PartnerConversation` from the top-level inbound SMS router and resolves which concierge sub-service handles the message, based on `conversation.conversationType` (`NEW_DOWNLOAD` or `ORIENTATION_PASSED`). There are two inbound paths — new-download and orientation-passed — each with its own gate sequence and its own fallback direction.

## Path 1: Inbound on a `new_download` conversation

```
Inbound SMS arrives on a NEW_DOWNLOAD conversation
  │
  ▼
Is orientationPassed.enabled? (LD kill-switch)
  │── No → handle on new_download agent
  │
  ▼
passesLocationGate(...)? (whitelist OR h3Geohashes/h3Rings — see Location Gate below)
  │── No → handle on new_download agent
  │
  ▼
computeEnabledOpStates(...): any lifecycle entries with stage !== 'none' AND
matching an entry in opCompletedEnabledProjects?
  │── No (empty list) → handle on new_download agent
  │
  ▼
Look up an EXISTING orientation_passed conversation doc for this phone number
(findByPhoneNumberAndType)
  │── None exists → DROP the inbound (see "First Crossover" below — do NOT
  │                  create one here, do NOT forward to new_download)
  │
  ▼
Close the new_download conversation (status → CLOSED, if not already)
  │
  ▼
Route to orientation_passed agent (ConciergeOrientationPassedService.handleInboundMessage)
```

## Path 2: Inbound on an `orientation_passed` conversation

```
Inbound SMS arrives on an ORIENTATION_PASSED conversation
  │
  ▼
Is orientationPassed.enabled? (LD kill-switch)
  │── No → routeOpInboundToNewDownload (see "Reverse Path" below)
  │
  ▼
passesLocationGate(...)?
  │── No → routeOpInboundToNewDownload
  │
  ▼
computeEnabledOpStates(...) (recomputed on every inbound — no early exit here
even if empty)
  │
  ▼
Route to orientation_passed agent
```

## First Crossover (new_download → orientation_passed)

**The outreach service is the SOLE creator of `orientation_passed` conversation documents.** `ConciergeDispatchService` never creates one on the inbound path. When a `new_download`-side inbound clears every gate (kill-switch, location, `opCompletedEnabledProjects`) but `findByPhoneNumberAndType` finds no existing `orientation_passed` doc for that phone number, the inbound is **dropped** — not routed to either concierge, not used to create a new OP+ conversation.

Why: an OP+-eligible partner with no OP+ doc means the OP+ outreach hasn't reached them yet (LD audience lag, pubsub race, opt-out, etc.). Forwarding that inbound to new_download would re-introduce the exact misrouted-yes flood the OP+ gate exists to prevent — a partner replying "yes" to old new_download copy while actually meaning to respond to shift-booking framing they haven't received yet. So the crossover is one-directional and outreach-initiated: `orientation_passed` conversations only ever come into existence via the outreach send path, never via this dispatcher.

Once an `orientation_passed` doc exists for a phone number, the new_download conversation is closed (`CLOSED`) the first time an inbound clears all the gates, and every subsequent inbound on that phone number routes through Path 2.

## Reverse Path (orientation_passed → new_download)

`routeOpInboundToNewDownload` — fires whenever an `orientation_passed`-side inbound fails the kill-switch or the location gate (there is no `opCompletedEnabledProjects` re-check on this direction; only `enabled` and the location gate can bounce it back):

```
1. Close the orientation_passed conversation (status → CLOSED, if not already)
2. Look up an existing new_download conversation for this phone number
   (findByPhoneNumberAndType)
3. If none exists, create one (currentState: ANSWERING_QS)
4. Route the inbound to the new_download agent on that conversation
```

This is the one case where the dispatcher itself creates a conversation document — always `new_download`, never `orientation_passed`.

## Location Gate (`OpEligibilityService.passesLocationGate`)

Shared by both inbound paths (and by the outbound OP+ trigger, which is out of scope here). Rules, in order:
1. **Whitelist bypass.** `senderPhone` in `config.routing.whitelistedPhoneNumbers` → always passes, regardless of location. Used for QA/prod canary.
2. **Empty geohash zone.** `h3Geohashes` empty → every non-whitelisted sender fails. The OP+ flag stays "on" but the audience collapses to the whitelist only.
3. **Non-empty geohash zone.** The partner's own h3 cell must fall inside the union of `gridDisk(seed, h3Rings)` for every configured seed. A partner with no stored h3 cell fails silently (logged, not surfaced to the partner).

`enabled` (the master kill-switch) is checked by the caller, not inside `passesLocationGate` — the two inbound paths have different fallback behavior when disabled (Path 1 falls back to new_download by skipping the gate check entirely; Path 2 explicitly reverse-routes), so each path handles the kill-switch itself before calling the gate.

## OP-Completed Eligibility (`findEnabledOpStates`)

Maps to: `src/modules/concierge-dispatch/services/op-completed-eligibility.ts`

A partner's lifecycle entry is OP+-eligible when **both**:
- `isOpOrHigher(stage)` — the stage is anything other than `'none'`. This is **not an ordinal/tier system** — there's no "OP or higher than OP" ranking to walk; the only distinction is "has an orientation-passed-or-later stage" (`stage !== 'none'`) vs. `'none'`.
- That entry's `(companyId, projectId, roleId)` tuple appears in `opCompletedEnabledProjects` (LD config).

`findEnabledOpStates(lifecycle, enabledProjects)` filters the partner's full lifecycle-state list down to just the matching entries; the filtered list is what gets passed to the orientation-passed agent as `enabledOpStates` and rendered into the `## Partner Information` block — see [`../concierge-orientation-passed/services/partner-information.md`](../concierge-orientation-passed/services/partner-information.md).

## LaunchDarkly Config Shape

The flag is `AGENTIC_PARTNER_CONCIERGE_CONFIG`. `opCompletedEnabledProjects`, `h3Geohashes`, and `h3Rings` nest under `orientationPassed.routing.*` — NOT flat on `orientationPassed` as previously documented.

```json
{
  "enabled": true,
  "dispatch": {
    "h3Rings": 5,
    "microserviceDispatchEnabled": false,
    "outreachDelayMinutes": 10,
    "quietHoursEnabled": false
  },
  "newDownload": {
    "llmConfig": { "finalResponseTemperature": 0.3 }
  },
  "orientationPassed": {
    "enabled": true,
    "quietHoursEnabled": false,
    "llmConfig": {
      "finalResponseTemperature": 0.3,
      "toolCallReasoningEffort": "off",
      "toolCallTemperature": 0.3
    },
    "routing": {
      "h3Geohashes": [],
      "h3Rings": 5,
      "opCompletedEnabledProjects": [
        { "companyId": "...", "projectId": "...", "roleId": "..." }
      ],
      "whitelistedPhoneNumbers": []
    },
    "triggers": {
      "enabled": false,
      "engagedNoBooking": { "enabled": false },
      "noEngagement": { "enabled": false },
      "shiftSearchRadiusMiles": 25
    }
  }
}
```

Key points:
- `orientationPassed.enabled: false` → kill-switch; Path 1 skips straight to new_download, Path 2 reverse-routes via `routeOpInboundToNewDownload`.
- `orientationPassed.routing.opCompletedEnabledProjects: []` → no partners are eligible for orientation-passed (Path 1 only — Path 2 doesn't re-check this list).
- `orientationPassed.routing.h3Geohashes: []` → geo gate rejects everyone except `whitelistedPhoneNumbers`.
- `orientationPassed.routing.whitelistedPhoneNumbers` → bypasses the geo gate entirely (not documented locally before).
- `orientationPassed.quietHoursEnabled` → gates OP+ *outreach* sends (not inbound routing) against the 10 PM–8 AM local quiet window; in-window sends defer to 8:01 AM local via a dedicated queue.
- `orientationPassed.triggers` → per-trigger enablement for the post-outreach nudge job (July 2026 ops doc, Triggers 1a/1b): `triggers.enabled` is the master switch for the whole nudge feature, `engagedNoBooking` (1a) and `noEngagement` (1b) gate the two nudge framings independently. This is a future/in-progress feature — the audience for it still rides `routing.opCompletedEnabledProjects` + `whitelistedPhoneNumbers`; it's not a distinct routing gate. T2/T3 trigger switches are deferred (not yet in this config).
- Defaults for everything above (`DEFAULT_PARTNER_CONCIERGE_CONFIG`) ship with the whole feature off (`enabled: false`, `orientationPassed.enabled: false`, empty routing arrays) — LD payload keys are optional and merge over these defaults, so a partial LD payload is safe.

## Dormant / Re-engagement (state machine, not the dispatcher)

Maps to: `src/modules/concierge-orientation-passed/state-machine/conversation-state-machine.ts`

The `orientation_passed` conversation-state transition table is intentionally minimal:
```
op_completed → dormant   (on INACTIVITY_TIMEOUT, 72h — see op-completed.md)
dormant      → (no outbound transitions)
```
`dormant`'s transition entry is an **empty object** in prod — there is currently no automated re-entry path out of `dormant` for the orientation-passed agent. A re-engagement job is documented as future work, not yet implemented. Do not assume dormant partners get any automatic OP+ nudge cadence beyond what `triggers` describes above (which fires *before* dormancy, not after).
