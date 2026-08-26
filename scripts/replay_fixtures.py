#!/usr/bin/env python3
"""
Concierge fixture replay harness.

Reads tests/fixtures/concierge_replay.yaml, builds the prompt for each fixture
via draft_service.assemble_prompt(), invokes the Claude CLI on the configured
model (default: haiku, for production-Flash parity), and applies per-fixture
assertions to the model output.

Run:
  python3 scripts/replay_fixtures.py                  # all fixtures
  python3 scripts/replay_fixtures.py walter allison   # only matching ids/names
  python3 scripts/replay_fixtures.py --model sonnet   # override model

Exits non-zero if any fixture fails.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path

import yaml

WORKSPACE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE))

from server.config import CLAUDE_CLI_PATH  # noqa: E402
from server.services.draft_service import assemble_prompt  # noqa: E402

DEFAULT_FIXTURES_PATH = WORKSPACE / "tests" / "fixtures" / "concierge_replay.yaml"
OUTPUT_DIR = WORKSPACE / "tests" / "fixtures" / "output"
DEFAULT_MODEL = "haiku"
TIMEOUT_SEC = 120

# Hard rules block in the prompt may produce literally empty output.
# We strip wrapping quotes/whitespace before assertions.
QUOTE_CHARS = ('"', "'", "`")


def load_fixtures(fixtures_path=None):
    path = Path(fixtures_path) if fixtures_path else DEFAULT_FIXTURES_PATH
    if not path.exists():
        print(f"ERROR: fixtures not found at {path}", file=sys.stderr)
        sys.exit(2)
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("fixtures", [])


def build_messages(fixture):
    """Convert YAML message list to assemble_prompt's message dict format."""
    messages = []
    for i, m in enumerate(fixture["messages"]):
        direction = m["from"]
        if direction == "partner":
            direction = "inbound"
        elif direction in ("concierge", "agent", "us"):
            direction = "outbound"
        messages.append({
            "direction": direction,
            "content": m["content"],
            "ts": m.get("ts") or f"2026-04-29 00:00:{i:02d}",
        })
    return messages


async def run_claude(prompt: str, model: str) -> tuple[str, str, int]:
    proc = await asyncio.create_subprocess_exec(
        CLAUDE_CLI_PATH, "-p", "--model", model,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=prompt.encode()),
            timeout=TIMEOUT_SEC,
        )
    except asyncio.TimeoutError:
        proc.kill()
        return "", "TIMEOUT", -1
    return stdout.decode("utf-8", errors="replace"), stderr.decode("utf-8", errors="replace"), proc.returncode


def clean_output(raw: str) -> str:
    """Strip wrapping quotes, trailing whitespace, code fences."""
    s = raw.strip()
    # Strip leading/trailing code fences
    s = re.sub(r"^```[a-zA-Z]*\n", "", s)
    s = re.sub(r"\n```$", "", s)
    s = s.strip()
    # Strip wrapping quotes
    if len(s) >= 2 and s[0] in QUOTE_CHARS and s[-1] == s[0]:
        s = s[1:-1].strip()
    return s


def parse_structured(raw: str):
    """Parse the structured {"intent": ..., "response": ...} JSON contract used by
    state-aware (orientation-passed) replays. Returns (intent, response, error).
    error is None on success; on failure intent is None and response is the raw
    output so text assertions still get something meaningful to chew on."""
    s = raw.strip()
    obj = None
    try:
        obj = json.loads(s)
    except (json.JSONDecodeError, ValueError):
        # Model wrapped the JSON in prose/fences — grab the first {...} blob.
        m = re.search(r"\{.*\}", s, re.DOTALL)
        if m:
            try:
                obj = json.loads(m.group(0))
            except (json.JSONDecodeError, ValueError):
                obj = None
    if not isinstance(obj, dict) or "intent" not in obj:
        return None, raw, f"structured parse: no intent field in output {s[:120]!r}"
    return obj.get("intent"), obj.get("response") or "", None


NO_SEND_EQUIVALENTS = {
    '""', "''",
    "(empty)", "[empty]", "(empty string)", "(empty response)", "[empty response]",
    "[blank]", "(blank)",
    "(no reply)", "[no reply]", "no reply",
    "(no response)", "[no response]", "no response",
    "(no message)", "[no message]", "no message", "no message.",
    "(no message to send)", "[no message to send]",
    "(no output)", "[no output]",
    "(silence)", "[silence]",
    "(none)", "[none]",
    "(suppressed)", "[suppressed]",
}
NO_SEND_KEYWORDS = re.compile(
    r"(?:rule\s*19|hard\s*rule\s*1\b|should\s+not\s+respond|no.?response|no.?repl(?:y|ies)|no\s+message|not\s+respond|bare\s+affirm|tapback|suppress.*delivery|output\s+nothing|zero\s+characters|empty\s+string)",
    re.IGNORECASE,
)


def is_no_send(output: str) -> bool:
    """True when the model is visibly declining to send (empty-equivalent
    placeholder or meta-commentary about the no-response rules). The SMS layer
    treats all of these as a no-send, so assertions must too — meta-commentary
    often QUOTES the conversation it is declining to answer, which would
    otherwise false-trip content assertions."""
    s = output.strip()
    if not s:
        return True
    if s.lower() in {e.lower() for e in NO_SEND_EQUIVALENTS}:
        return True
    return bool(NO_SEND_KEYWORDS.search(s))


def apply_assertions(output: str, expected: dict) -> list[str]:
    """Return list of failure messages; empty list = pass."""
    failures = []

    # Models sometimes emit the structured {"intent", "response"} envelope even
    # on legacy (non-state) fixtures — the SMS layer would send only the
    # response field, so assertions run against that.
    if output.lstrip().startswith("{"):
        _intent, _resp, _err = parse_structured(output)
        if _err is None:
            output = _resp.strip()

    if output.strip() and is_no_send(output):
        output = ""

    if "must_be_empty" in expected:
        if output.strip() and not is_no_send(output):
            failures.append(f"must_be_empty: got non-empty {output.strip()!r}")
        else:
            output = ""

    if "must_equal" in expected:
        target = expected["must_equal"].strip()
        if output.strip() != target:
            failures.append(f"must_equal: expected {target!r}, got {output.strip()!r}")

    for needle in expected.get("must_contain", []):
        if needle.lower() not in output.lower():
            failures.append(f"must_contain {needle!r} — not in output")

    for needle in expected.get("must_not_contain", []):
        if needle.lower() in output.lower():
            failures.append(f"must_not_contain {needle!r} — present in output")

    for pattern in expected.get("regex_match", []):
        if not re.search(pattern, output, re.IGNORECASE):
            failures.append(f"regex_match {pattern!r} — no match")

    return failures


_PREFILTER_CACHE = None


def apply_prefilter(last_inbound: str):
    """Simulate production's pre-LLM keyword prefilter (keyword-prefilter.ts).

    Only the deterministic opt_out and profanity_abuse filters are simulated —
    matches never reach the LLM in production, so replays shouldn't send them
    either. prompt_injection and simple_reply are intentionally NOT simulated:
    injection fixtures exist to test the LLM's own resilience, and simple_reply's
    firing conditions are state-dependent in prod (not yet mirrored here).
    Returns (filter_name, response) or None."""
    global _PREFILTER_CACHE
    if _PREFILTER_CACHE is None:
        pf_path = Path(__file__).resolve().parent.parent / "common" / "concierge" / "keyword-prefilter.json"
        with open(pf_path) as f:
            _PREFILTER_CACHE = json.load(f)
    for filt in _PREFILTER_CACHE.get("filters", []):
        if filt.get("name") not in ("opt_out", "profanity_abuse"):
            continue
        for pat in filt.get("patterns", []):
            if re.search(pat, last_inbound):
                return filt["name"], filt.get("response", "")
    return None


async def run_fixture(fixture, model: str, save_dir: Path):
    name = fixture.get("name", fixture.get("partner_id", "?"))
    first_name = fixture.get("first_name", "")
    messages = build_messages(fixture)
    # Opt-in state-aware replay: a `state` key (e.g. op_completed) injects the
    # funnel-stage prompt and switches to the structured JSON output contract.
    # (Distinct from the legacy `status` key, which is xlsx metadata only.)
    state = fixture.get("state", "")
    # Opt-in DxGy replay: an `offer_context` key injects the production-shaped
    # `## Active Bonus Offer` block. Absent/empty = no active offer, which is
    # itself the signal HARD RULE 31 keys off.
    offer_context = fixture.get("offer_context", "")
    prompt = assemble_prompt(messages, first_name, "", state=state, offer_context=offer_context)
    if not prompt:
        return name, "ERROR", ["empty prompt"], "", "", 0.0

    # Production pipeline order: keyword prefilter fires BEFORE the LLM.
    last_inbound = next(
        (m["content"] for m in reversed(messages) if m["direction"] == "inbound"), ""
    )
    prefilter_hit = apply_prefilter(last_inbound)

    if prefilter_hit:
        filter_name, output = prefilter_hit
        stdout, stderr, code, dt = output, "", 0, 0.0
        intent = filter_name
    else:
        t0 = time.time()
        stdout, stderr, code = await run_claude(prompt, model)
        dt = time.time() - t0
        output = clean_output(stdout)
        intent = None

    failures = []

    if code != 0 and not output:
        failures.append(f"claude exit code {code}: {stderr[:200]}")

    expected = fixture.get("expected", {})

    if state and not prefilter_hit:
        intent, response_text, parse_err = parse_structured(output)
        if parse_err:
            failures.append(parse_err)
        else:
            output = response_text.strip()

    if "intent_must_equal" in expected:
        target = expected["intent_must_equal"]
        if intent != target:
            failures.append(f"intent_must_equal: expected {target!r}, got {intent!r}")

    if "intent_in" in expected:
        allowed = expected["intent_in"]
        if intent not in allowed:
            failures.append(f"intent_in: expected one of {allowed!r}, got {intent!r}")

    failures.extend(apply_assertions(output, expected))

    # Save transcript
    save_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    out_path = save_dir / f"{safe_name}.txt"
    with open(out_path, "w") as f:
        f.write(f"# Fixture: {name}\n")
        f.write(f"# Model: {model}\n")
        f.write(f"# Duration: {dt:.1f}s\n")
        f.write(f"# Exit: {code}\n")
        if prefilter_hit:
            f.write(f"# Prefilter: {prefilter_hit[0]} (deterministic, no LLM call)\n")
        if state:
            f.write(f"# State: {state}\n")
            f.write(f"# Intent: {intent}\n")
        if offer_context:
            f.write("# OfferContext: yes\n")
        f.write(f"# Failures: {len(failures)}\n")
        for fail in failures:
            f.write(f"#   - {fail}\n")
        f.write("\n## CONVERSATION\n")
        for m in messages:
            role = "Partner" if m["direction"] == "inbound" else "Concierge"
            f.write(f"{role}: {m['content']}\n")
        f.write("\n## CONCIERGE OUTPUT\n")
        f.write(output if output else "(empty)\n")
        if stderr:
            f.write("\n## STDERR\n")
            f.write(stderr)

    status = "PASS" if not failures else "FAIL"
    return name, status, failures, output, str(out_path), dt


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filters", nargs="*", help="Substrings to match against fixture name/partner_id")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--fixtures", default=None, help="Path to fixtures YAML file (default: concierge_replay.yaml)")
    args = parser.parse_args()

    fixtures = load_fixtures(args.fixtures)
    if args.filters:
        fixtures = [f for f in fixtures if any(s.lower() in (f.get("name", "") + f.get("partner_id", "")).lower() for s in args.filters)]

    if not fixtures:
        print("No fixtures matched filters")
        return 0

    print(f"Running {len(fixtures)} fixture(s) on model={args.model}, concurrency={args.concurrency}")
    print("-" * 80)

    sem = asyncio.Semaphore(args.concurrency)

    async def guarded(fx):
        async with sem:
            return await run_fixture(fx, args.model, OUTPUT_DIR)

    results = await asyncio.gather(*[guarded(fx) for fx in fixtures])

    # Print summary
    pass_count = 0
    fail_count = 0
    for name, status, failures, output, path, dt in results:
        marker = "✓" if status == "PASS" else "✗"
        print(f"{marker} [{status}] {name:40s} ({dt:.1f}s) → {path}")
        if failures:
            for fail in failures:
                print(f"      - {fail}")
            preview = output[:120].replace("\n", " ⏎ ")
            print(f"      output: {preview!r}")
            fail_count += 1
        else:
            pass_count += 1

    print("-" * 80)
    print(f"Pass: {pass_count}/{len(results)}    Fail: {fail_count}/{len(results)}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
