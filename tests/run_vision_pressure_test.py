#!/usr/bin/env python3
"""Vision preprocessor pressure test — 12 real screenshots through vision + concierge pipeline.

Calls Claude vision on each image, parses the analysis, routes through the concierge,
and generates a self-contained HTML report with embedded images.
"""

import base64
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# Ensure repo root is on sys.path so all imports resolve
REPO_ROOT = "/Users/prithvi/partner-outreach"
sys.path.insert(0, REPO_ROOT)

from experiments.vision.prompt import build_vision_prompt
from experiments.vision.types import ImageAnalysis, Message
from experiments.vision.format import format_analysis_for_prompt
from server.services.draft_service import assemble_prompt

# Paths
IMAGE_DIR = Path("/Users/prithvi/Downloads/vision preprocessor test images")
REPORT_PATH = Path(REPO_ROOT) / "tests" / "vision_pressure_test_report.html"
CLAUDE_CLI = "/Users/prithvi/.local/bin/claude"
PYTHON = os.path.expanduser("~/.venvs/adk/bin/python")


@dataclass
class TestResult:
    image_name: str
    image_path: str
    b64_image: str = ""
    # Vision
    vision_raw: str = ""
    vision_error: str = ""
    vision_duration: float = 0.0
    analysis: ImageAnalysis | None = None
    analysis_block: str = ""
    # Concierge
    concierge_response: str = ""
    concierge_error: str = ""
    concierge_duration: float = 0.0


def call_claude_vision(image_path: str, prompt_text: str) -> tuple[str, float]:
    """Call claude CLI with an image file and return (response_text, duration_seconds).

    Uses --add-dir to grant file access so Claude can read the image via its
    built-in Read tool, then applies the vision analysis prompt.
    """
    image_dir = str(Path(image_path).parent)
    image_filename = Path(image_path).name

    # Wrap the vision prompt: instruct Claude to read the image first, then analyze
    full_prompt = (
        f"First, read the image file at this path: {image_path}\n"
        f"Then analyze it according to these instructions:\n\n"
        f"{prompt_text}"
    )

    t0 = time.time()
    try:
        result = subprocess.run(
            [
                CLAUDE_CLI, "-p", "--model", "sonnet",
                "--output-format", "json",
                "--add-dir", image_dir,
                "--dangerously-skip-permissions",
                "--allowedTools", "Read",
            ],
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=120,
        )
        duration = time.time() - t0
        if result.returncode != 0:
            return f"ERROR (rc={result.returncode}): {result.stderr.strip()}", duration
        response = json.loads(result.stdout)
        text = response.get("result", "")
        return text, duration
    except subprocess.TimeoutExpired:
        return "ERROR: Timeout after 120s", time.time() - t0
    except json.JSONDecodeError as e:
        return f"ERROR: JSON decode failed: {e}\nRaw stdout: {result.stdout[:500]}", time.time() - t0
    except Exception as e:
        return f"ERROR: {e}", time.time() - t0


def call_claude_text(prompt_text: str) -> tuple[str, float]:
    """Call claude CLI with text-only prompt and return (response_text, duration_seconds)."""
    t0 = time.time()
    try:
        result = subprocess.run(
            [CLAUDE_CLI, "-p", "--model", "sonnet", "--output-format", "json"],
            input=prompt_text,
            capture_output=True,
            text=True,
            timeout=120,
        )
        duration = time.time() - t0
        if result.returncode != 0:
            return f"ERROR (rc={result.returncode}): {result.stderr.strip()}", duration
        response = json.loads(result.stdout)
        text = response.get("result", "")
        return text, duration
    except subprocess.TimeoutExpired:
        return "ERROR: Timeout after 120s", time.time() - t0
    except json.JSONDecodeError as e:
        return f"ERROR: JSON decode failed: {e}\nRaw stdout: {result.stdout[:500]}", time.time() - t0
    except Exception as e:
        return f"ERROR: {e}", time.time() - t0


def parse_analysis_json(raw: str) -> ImageAnalysis | None:
    """Extract JSON from Claude's response (may be wrapped in code fences)."""
    if raw.startswith("ERROR"):
        return None
    # Strip markdown code fences
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", raw.strip())
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    cleaned = cleaned.strip()
    try:
        data = json.loads(cleaned)
        return ImageAnalysis(**data)
    except (json.JSONDecodeError, Exception) as e:
        print(f"  [WARN] Could not parse analysis JSON: {e}")
        print(f"  [WARN] Raw text (first 300 chars): {cleaned[:300]}")
        return None


def build_concierge_prompt(analysis_block: str) -> str:
    """Build a minimal concierge prompt with vision analysis prepended."""
    # Minimal conversation: one outbound welcome + one inbound image placeholder
    messages = [
        {"direction": "outbound", "content": "Hey! Welcome to Shiftsmart. Let me know if you have any questions as you get started.", "ts": "2026-05-21T10:00:00"},
        {"direction": "inbound", "content": "(image)", "ts": "2026-05-21T10:05:00"},
    ]

    base_prompt = assemble_prompt(messages, first_name="Partner", campaign_context="")

    # Prepend the vision analysis block right after the system identity line
    # Insert vision block before the HARD RULES section
    full_prompt = f"{analysis_block}\n\n{base_prompt}"
    return full_prompt


def encode_image_b64(image_path: str) -> str:
    """Read image file and return base64 encoded string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def run_test(image_path: str, image_name: str, idx: int) -> TestResult:
    """Run vision + concierge pipeline for a single image."""
    print(f"\n{'='*60}")
    print(f"[{idx}/12] Processing: {image_name}")
    print(f"{'='*60}")

    result = TestResult(image_name=image_name, image_path=image_path)
    result.b64_image = encode_image_b64(image_path)

    # Step 1: Vision call
    print(f"  [1/3] Calling Claude vision...")
    vision_prompt = build_vision_prompt(
        partner_state="answering_qs",
        partner_message=None,
        conversation_history=[],
    )
    raw_response, duration = call_claude_vision(image_path, vision_prompt)
    result.vision_raw = raw_response
    result.vision_duration = duration
    print(f"  Vision done in {duration:.1f}s")

    if raw_response.startswith("ERROR"):
        result.vision_error = raw_response
        print(f"  [ERROR] Vision failed: {raw_response[:200]}")
        return result

    # Step 2: Parse analysis
    print(f"  [2/3] Parsing analysis...")
    analysis = parse_analysis_json(raw_response)
    if analysis is None:
        result.vision_error = f"Failed to parse: {raw_response[:200]}"
        print(f"  [ERROR] Parse failed")
        return result

    result.analysis = analysis
    print(f"  Screen: {analysis.screen_id} (confidence: {analysis.confidence})")
    print(f"  App screenshot: {analysis.is_app_screenshot}")

    # Step 3: Format and route through concierge
    print(f"  [3/3] Routing through concierge...")
    analysis_block = format_analysis_for_prompt(analysis)
    result.analysis_block = analysis_block

    concierge_prompt = build_concierge_prompt(analysis_block)
    concierge_text, c_duration = call_claude_text(concierge_prompt)
    result.concierge_duration = c_duration

    if concierge_text.startswith("ERROR"):
        result.concierge_error = concierge_text
        print(f"  [ERROR] Concierge failed: {concierge_text[:200]}")
    else:
        result.concierge_response = concierge_text
        print(f"  Concierge response ({len(concierge_text)} chars): {concierge_text[:100]}...")

    print(f"  Total time: {result.vision_duration + result.concierge_duration:.1f}s")
    return result


def generate_html_report(results: list[TestResult]) -> str:
    """Generate a self-contained HTML report."""

    # Summary stats
    total = len(results)
    app_screenshots = sum(1 for r in results if r.analysis and r.analysis.is_app_screenshot)
    non_app = sum(1 for r in results if r.analysis and not r.analysis.is_app_screenshot)
    parse_failures = sum(1 for r in results if r.analysis is None)
    confidences = [r.analysis.confidence for r in results if r.analysis]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    low_confidence = sum(1 for c in confidences if c < 0.5)
    concierge_errors = sum(1 for r in results if r.concierge_error)
    total_vision_time = sum(r.vision_duration for r in results)
    total_concierge_time = sum(r.concierge_duration for r in results)

    # Build cards
    cards_html = ""
    for i, r in enumerate(results):
        bg = "#f8f9fa" if i % 2 == 0 else "#ffffff"

        # Analysis details
        if r.analysis:
            a = r.analysis
            analysis_html = f"""
            <div class="analysis-grid">
                <div class="analysis-item">
                    <span class="label">Screen ID</span>
                    <span class="value">{_esc(a.screen_id)}</span>
                </div>
                <div class="analysis-item">
                    <span class="label">App Screenshot</span>
                    <span class="value {'yes' if a.is_app_screenshot else 'no'}">{a.is_app_screenshot}</span>
                </div>
                <div class="analysis-item">
                    <span class="label">Confidence</span>
                    <span class="value">{_confidence_badge(a.confidence)}</span>
                </div>
                <div class="analysis-item full-width">
                    <span class="label">Visible Elements</span>
                    <span class="value">{_esc(a.visible_elements)}</span>
                </div>
                <div class="analysis-item full-width">
                    <span class="label">Error State</span>
                    <span class="value">{_esc(str(a.error_state)) if a.error_state else '<em>None</em>'}</span>
                </div>
                <div class="analysis-item full-width">
                    <span class="label">Partner Problem</span>
                    <span class="value">{_esc(a.partner_problem)}</span>
                </div>
                <div class="analysis-item full-width">
                    <span class="label">Suggested Action</span>
                    <span class="value">{_esc(a.suggested_action)}</span>
                </div>
            </div>"""
        elif r.vision_error:
            analysis_html = f'<div class="error-box">{_esc(r.vision_error[:500])}</div>'
        else:
            analysis_html = '<div class="error-box">No analysis available</div>'

        # Concierge response
        if r.concierge_response:
            concierge_html = f'<div class="concierge-bubble">{_esc(r.concierge_response)}</div>'
        elif r.concierge_error:
            concierge_html = f'<div class="error-box">{_esc(r.concierge_error[:500])}</div>'
        else:
            concierge_html = '<div class="error-box">No concierge response (vision failed)</div>'

        cards_html += f"""
        <div class="card" style="background: {bg};">
            <div class="card-header">
                <h2>Test {i+1}: {_esc(r.image_name)}</h2>
                <div class="timing">
                    <span>Vision: {r.vision_duration:.1f}s</span>
                    <span>Concierge: {r.concierge_duration:.1f}s</span>
                </div>
            </div>
            <div class="card-body">
                <div class="image-col">
                    <img src="data:image/jpeg;base64,{r.b64_image}" alt="{_esc(r.image_name)}"
                         style="max-width:300px; max-height:600px; border-radius:12px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);">
                </div>
                <div class="details-col">
                    <h3>Vision Analysis</h3>
                    {analysis_html}
                    <h3 style="margin-top: 20px;">Concierge Response</h3>
                    {concierge_html}
                </div>
            </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vision Preprocessor Pressure Test — {total} Images</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #eef1f5; color: #333; }}
    .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: #fff; padding: 40px 30px; }}
    .header h1 {{ font-size: 28px; margin-bottom: 8px; }}
    .header .subtitle {{ color: #94a3b8; font-size: 14px; }}
    .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; padding: 24px 30px; background: #fff; border-bottom: 1px solid #e2e8f0; }}
    .stat {{ text-align: center; }}
    .stat .num {{ font-size: 32px; font-weight: 700; color: #0f3460; }}
    .stat .desc {{ font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 24px 16px; }}
    .card {{ border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); margin-bottom: 24px; overflow: hidden; }}
    .card-header {{ display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-bottom: 1px solid #e2e8f0; }}
    .card-header h2 {{ font-size: 18px; color: #1a1a2e; }}
    .timing {{ display: flex; gap: 16px; font-size: 12px; color: #64748b; }}
    .timing span {{ background: #f1f5f9; padding: 4px 10px; border-radius: 6px; }}
    .card-body {{ display: flex; gap: 24px; padding: 24px; }}
    .image-col {{ flex-shrink: 0; }}
    .details-col {{ flex: 1; min-width: 0; }}
    .details-col h3 {{ font-size: 15px; color: #0f3460; margin-bottom: 12px; font-weight: 600; }}
    .analysis-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }}
    .analysis-item {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; }}
    .analysis-item.full-width {{ grid-column: 1 / -1; }}
    .analysis-item .label {{ display: block; font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.3px; margin-bottom: 4px; }}
    .analysis-item .value {{ font-size: 14px; color: #1e293b; }}
    .analysis-item .value.yes {{ color: #16a34a; font-weight: 600; }}
    .analysis-item .value.no {{ color: #dc2626; font-weight: 600; }}
    .concierge-bubble {{ background: #e8f4fd; border-left: 4px solid #3b82f6; padding: 14px 18px; border-radius: 0 8px 8px 0; font-size: 14px; line-height: 1.6; color: #1e293b; white-space: pre-wrap; }}
    .error-box {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 12px 16px; border-radius: 0 8px 8px 0; font-size: 13px; color: #991b1b; font-family: monospace; white-space: pre-wrap; }}
    .confidence-badge {{ display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 13px; font-weight: 600; }}
    .conf-high {{ background: #dcfce7; color: #166534; }}
    .conf-med {{ background: #fef9c3; color: #854d0e; }}
    .conf-low {{ background: #fecaca; color: #991b1b; }}
    @media (max-width: 768px) {{
        .card-body {{ flex-direction: column; }}
        .analysis-grid {{ grid-template-columns: 1fr; }}
    }}
</style>
</head>
<body>
<div class="header">
    <h1>Vision Preprocessor Pressure Test</h1>
    <div class="subtitle">12 real partner screenshots — vision analysis + concierge routing — {time.strftime('%Y-%m-%d %H:%M')}</div>
</div>
<div class="summary">
    <div class="stat"><div class="num">{total}</div><div class="desc">Total Images</div></div>
    <div class="stat"><div class="num">{app_screenshots}</div><div class="desc">App Screenshots</div></div>
    <div class="stat"><div class="num">{non_app}</div><div class="desc">Non-App</div></div>
    <div class="stat"><div class="num">{parse_failures}</div><div class="desc">Parse Failures</div></div>
    <div class="stat"><div class="num">{avg_confidence:.0%}</div><div class="desc">Avg Confidence</div></div>
    <div class="stat"><div class="num">{low_confidence}</div><div class="desc">Low Confidence (&lt;0.5)</div></div>
    <div class="stat"><div class="num">{total_vision_time:.0f}s</div><div class="desc">Total Vision Time</div></div>
    <div class="stat"><div class="num">{total_concierge_time:.0f}s</div><div class="desc">Total Concierge Time</div></div>
</div>
<div class="container">
{cards_html}
</div>
</body>
</html>"""
    return html


def _esc(text: str) -> str:
    """HTML-escape text."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _confidence_badge(conf: float) -> str:
    """Return a colored confidence badge."""
    if conf >= 0.7:
        cls = "conf-high"
    elif conf >= 0.5:
        cls = "conf-med"
    else:
        cls = "conf-low"
    return f'<span class="confidence-badge {cls}">{conf:.0%}</span>'


def main():
    print("Vision Preprocessor Pressure Test")
    print("=" * 60)

    # Discover images
    images = []
    for i in range(1, 13):
        path = IMAGE_DIR / f"test{i}.jpeg"
        if path.exists():
            images.append((f"test{i}.jpeg", str(path)))
        else:
            print(f"[WARN] Missing: {path}")

    print(f"Found {len(images)} images")

    # Run tests sequentially
    results = []
    for idx, (name, path) in enumerate(images, 1):
        result = run_test(path, name, idx)
        results.append(result)

    # Generate report
    print(f"\n{'='*60}")
    print("Generating HTML report...")
    html = generate_html_report(results)
    REPORT_PATH.write_text(html)
    print(f"Report saved to: {REPORT_PATH}")

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    total = len(results)
    app_ss = sum(1 for r in results if r.analysis and r.analysis.is_app_screenshot)
    fails = sum(1 for r in results if r.analysis is None)
    confs = [r.analysis.confidence for r in results if r.analysis]
    avg_c = sum(confs) / len(confs) if confs else 0
    low_c = sum(1 for c in confs if c < 0.5)
    print(f"  Total images:       {total}")
    print(f"  App screenshots:    {app_ss}")
    print(f"  Non-app:            {total - app_ss - fails}")
    print(f"  Parse failures:     {fails}")
    print(f"  Avg confidence:     {avg_c:.0%}")
    print(f"  Low confidence:     {low_c}")
    print(f"  Total time:         {sum(r.vision_duration + r.concierge_duration for r in results):.0f}s")

    for r in results:
        sid = r.analysis.screen_id if r.analysis else "FAILED"
        conf = f"{r.analysis.confidence:.0%}" if r.analysis else "N/A"
        print(f"  {r.image_name:15s}  {sid:35s}  conf={conf}")


if __name__ == "__main__":
    main()
