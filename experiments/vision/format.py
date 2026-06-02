# experiments/vision/format.py
from __future__ import annotations

from experiments.vision.taxonomy import screen_id_description
from experiments.vision.types import ImageAnalysis


def format_analysis_for_prompt(analysis: ImageAnalysis, image_count: int = 1) -> str:
    if not analysis.is_app_screenshot:
        return (
            "## Image Analysis\n"
            "The partner sent an image that is not a Shiftsmart app screenshot.\n"
            "Respond to their text message normally. If they have no text, ask what they need help with."
        )

    if analysis.confidence < 0.5:
        return (
            "## Image Analysis\n"
            f"The partner sent {image_count} screenshot(s) but the vision system is "
            "not sure which screen it shows.\n"
            "Ask the partner to describe what they see on their screen."
        )

    hedged = analysis.confidence < 0.7
    hedge_prefix = "It looks like the partner might be on" if hedged else "Screen:"

    error_line = f"Error state: {analysis.error_state}" if analysis.error_state else "Error state: None"

    return (
        f"## Image Analysis\n"
        f"The partner sent {image_count} screenshot(s).\n\n"
        f"{hedge_prefix} {analysis.screen_id} — {screen_id_description(analysis.screen_id)}\n"
        f"Visible elements: {analysis.visible_elements}\n"
        f"{error_line}\n"
        f"Partner's likely problem: {analysis.partner_problem}\n"
        f"Suggested next step: {analysis.suggested_action}\n"
        f"Confidence: {analysis.confidence}\n\n"
        f"IMPORTANT: The vision system has analyzed the partner's screenshot. "
        f"Do NOT use the image_or_screenshot intent or say you cannot see images. "
        f"You CAN see what they sent. Use the analysis above to respond with "
        f"specific, actionable guidance based on what their screen shows."
    )
