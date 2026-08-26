# Vision Preprocessor — Experiment

> **Status: experiment, limited scope.** I (PK) only worked on this with limited scope — it's mostly an experiment, not a production-track workstream. It was a local proof-of-concept to test whether a vision preprocessing step (analyzing partner-sent screenshots and injecting an `## Image Analysis` block into the concierge prompt) is viable before handing the idea to EPD. Nothing here is deployed, and none of it maps to production code in the monorepo.

## What it is

A provider-interface harness (`VisionProvider` ABC → `MockProvider` for deterministic tests, `ClaudeProvider` via `claude -p` subprocess) that:

1. Downloads and filters inbound MMS images
2. Runs vision analysis against a screen-ID taxonomy (`taxonomy.py`)
3. Formats the result into an `## Image Analysis` context block injected via the existing `assemble_prompt()`

See `docs/superpowers/plans/2026-05-21-vision-preprocessor-harness.md` for the original implementation plan and `tests/vision/` for fixtures.
