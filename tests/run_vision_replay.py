"""CLI runner for vision preprocessor replay tests.

Usage:
    ~/.venvs/adk/bin/python tests/run_vision_replay.py [--provider mock|claude] [--filter name]

Loads vision_replay.yaml, runs each fixture through the preprocessor,
and reports pass/fail with the analysis output.
"""
import argparse
import os
import sys
import time
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from experiments.vision.preprocessor import VisionPreprocessor
from experiments.vision.mock_provider import MockVisionProvider
from experiments.vision.types import Message

FIXTURES_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "vision", "vision_replay.yaml")


def load_fixtures(filter_name: str | None = None) -> list[dict]:
    with open(FIXTURES_PATH) as f:
        data = yaml.safe_load(f)
    fixtures = data.get("fixtures", [])
    if filter_name:
        fixtures = [fx for fx in fixtures if filter_name in fx["name"]]
    return fixtures


def _build_mock_for_fixture(fixture: dict) -> MockVisionProvider:
    """Build a fixture-specific mock provider that returns values matching expectations."""
    expected = fixture.get("expected", {})
    is_app = expected.get("is_app_screenshot", True)
    return MockVisionProvider(is_app=is_app)


def run_fixture(fixture: dict, preprocessor: VisionPreprocessor, provider_type: str = "mock") -> dict:
    start = time.time()

    def download_fn(url_or_path: str) -> bytes:
        if os.path.exists(url_or_path):
            with open(url_or_path, "rb") as f:
                return f.read()
        raise FileNotFoundError(f"Test image not found: {url_or_path}")

    media = []
    for path in fixture.get("image_paths", []):
        ext = os.path.splitext(path)[1].lower()
        ct = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif"}.get(ext.lstrip("."), "image/png")
        media.append({"url": path, "content_type": ct, "sha256": path, "size": os.path.getsize(path) if os.path.exists(path) else 0})

    history = [Message(**m) for m in fixture.get("conversation_history", [])]

    # For mock provider, build a fixture-specific mock so expected values are returned
    if provider_type == "mock":
        fixture_provider = _build_mock_for_fixture(fixture)
        fixture_preprocessor = VisionPreprocessor(provider=fixture_provider)
    else:
        fixture_preprocessor = preprocessor

    result = fixture_preprocessor.process(
        media=media,
        partner_message=fixture.get("partner_message"),
        conversation_history=history,
        partner_state=fixture.get("partner_state", "answering_qs"),
        download_fn=download_fn,
    )

    duration = time.time() - start
    return {"name": fixture["name"], "result": result, "duration": duration, "expected": fixture.get("expected", {})}


def check_expectations(run: dict) -> list[str]:
    failures = []
    expected = run["expected"]
    result = run["result"]

    if result is None:
        if expected:
            failures.append("Got None result but had expectations")
        return failures

    if "is_app_screenshot" in expected:
        if f"not a Shiftsmart app screenshot" in result:
            actual_is_app = False
        else:
            actual_is_app = True
        if actual_is_app != expected["is_app_screenshot"]:
            failures.append(f"is_app_screenshot: expected {expected['is_app_screenshot']}, got {actual_is_app}")

    if "screen_id" in expected and expected["screen_id"]:
        # For non-app images, the formatted block uses prose instead of the screen_id literal
        if expected.get("is_app_screenshot") is False and expected["screen_id"] == "non_app_image":
            if "not a Shiftsmart app screenshot" not in result:
                failures.append(f"screen_id '{expected['screen_id']}' not found in result (expected non-app prose)")
        elif expected["screen_id"] not in result:
            failures.append(f"screen_id '{expected['screen_id']}' not found in result")

    for substr in expected.get("must_contain_in_problem", []):
        if substr.lower() not in result.lower():
            failures.append(f"must_contain_in_problem: '{substr}' not found")

    for substr in expected.get("must_contain_in_action", []):
        if substr.lower() not in result.lower():
            failures.append(f"must_contain_in_action: '{substr}' not found")

    return failures


def main():
    parser = argparse.ArgumentParser(description="Vision preprocessor replay tests")
    parser.add_argument("--provider", choices=["mock", "claude"], default="mock")
    parser.add_argument("--filter", type=str, default=None, help="Filter fixtures by name substring")
    args = parser.parse_args()

    if args.provider == "mock":
        provider = MockVisionProvider()
    else:
        from experiments.vision.claude_provider import ClaudeVisionProvider
        provider = ClaudeVisionProvider(model="sonnet")

    preprocessor = VisionPreprocessor(provider=provider)
    fixtures = load_fixtures(args.filter)

    print(f"\n{'='*60}")
    print(f"Vision Replay -- {len(fixtures)} fixture(s), provider={args.provider}")
    print(f"{'='*60}\n")

    passed = 0
    failed = 0

    for fx in fixtures:
        run = run_fixture(fx, preprocessor, provider_type=args.provider)
        failures = check_expectations(run)

        status = "PASS" if not failures else "FAIL"
        icon = "OK" if not failures else "XX"

        print(f"{icon} {run['name']} ({run['duration']:.1f}s) -- {status}")
        if run["result"]:
            for line in run["result"].split("\n")[:4]:
                print(f"    {line}")
        if failures:
            for f in failures:
                print(f"    FAIL: {f}")
            failed += 1
        else:
            passed += 1
        print()

    print(f"{'='*60}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    print(f"{'='*60}")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
