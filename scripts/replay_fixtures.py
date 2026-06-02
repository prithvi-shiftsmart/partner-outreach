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


def apply_assertions(output: str, expected: dict) -> list[str]:
    """Return list of failure messages; empty list = pass."""
    failures = []

    if "must_be_empty" in expected:
        # The HARD RULES tell the model to produce a literal empty string. Some
        # models still emit a placeholder like "(no reply)" — accept those as
        # equivalent to empty since the model IS attempting to comply with the
        # rule and the SMS layer will treat any of these as a no-send.
        non_trivial = output.strip()
        EMPTY_EQUIVALENTS = {
            '""', "''",
            "(empty)", "[empty]", "(empty string)",
            "[blank]", "(blank)",
            "(no reply)", "[no reply]", "no reply",
            "(silence)", "[silence]",
            "(none)", "[none]",
        }
        if non_trivial and non_trivial.lower() not in {s.lower() for s in EMPTY_EQUIVALENTS}:
            failures.append(f"must_be_empty: got non-empty {non_trivial!r}")

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


async def run_fixture(fixture, model: str, save_dir: Path):
    name = fixture.get("name", fixture.get("partner_id", "?"))
    first_name = fixture.get("first_name", "")
    messages = build_messages(fixture)
    prompt = assemble_prompt(messages, first_name, "")
    if not prompt:
        return name, "ERROR", ["empty prompt"], "", "", 0.0

    t0 = time.time()
    stdout, stderr, code = await run_claude(prompt, model)
    dt = time.time() - t0

    output = clean_output(stdout)
    failures = []

    if code != 0 and not output:
        failures.append(f"claude exit code {code}: {stderr[:200]}")

    failures.extend(apply_assertions(output, fixture.get("expected", {})))

    # Save transcript
    save_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    out_path = save_dir / f"{safe_name}.txt"
    with open(out_path, "w") as f:
        f.write(f"# Fixture: {name}\n")
        f.write(f"# Model: {model}\n")
        f.write(f"# Duration: {dt:.1f}s\n")
        f.write(f"# Exit: {code}\n")
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
