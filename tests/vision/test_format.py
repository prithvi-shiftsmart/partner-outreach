# tests/vision/test_format.py
from experiments.vision.format import format_analysis_for_prompt
from experiments.vision.types import ImageAnalysis


def test_format_app_screenshot():
    analysis = ImageAnalysis(
        screen_id="shifts_tab_empty",
        visible_elements='Bottom nav: Home, Shifts (selected). Main area: "No shifts available near me"',
        error_state=None,
        partner_problem="No shifts available in partner's area",
        suggested_action="Tell partner to check back daily, do not suggest lock-icon fallback",
        confidence=0.92,
        is_app_screenshot=True,
    )
    text = format_analysis_for_prompt(analysis, image_count=1)
    assert "## Image Analysis" in text
    assert "shifts_tab_empty" in text
    assert "No shifts available" in text
    assert "0.92" in text
    assert "Do NOT use the image_or_screenshot intent" in text
    assert "You CAN see what they sent" in text


def test_format_non_app_image():
    analysis = ImageAnalysis(
        screen_id="non_app_image",
        visible_elements="Non-app content",
        error_state=None,
        partner_problem="Not an app screenshot",
        suggested_action="Respond to text normally",
        confidence=0.9,
        is_app_screenshot=False,
    )
    text = format_analysis_for_prompt(analysis, image_count=1)
    assert "## Image Analysis" in text
    assert "not a Shiftsmart app screenshot" in text
    assert "Respond to their text message normally" in text


def test_format_multiple_images():
    analysis = ImageAnalysis(
        screen_id="orientation_module_N",
        visible_elements="Module 3 of 9",
        error_state=None,
        partner_problem="Stuck mid-orientation",
        suggested_action="Provide module-specific coaching",
        confidence=0.8,
        is_app_screenshot=True,
    )
    text = format_analysis_for_prompt(analysis, image_count=3)
    assert "3 screenshot(s)" in text


def test_format_low_confidence():
    analysis = ImageAnalysis(
        screen_id="unidentifiable",
        visible_elements="Unclear",
        error_state=None,
        partner_problem="Cannot determine",
        suggested_action="Ask partner to describe",
        confidence=0.35,
        is_app_screenshot=True,
    )
    text = format_analysis_for_prompt(analysis, image_count=1)
    assert "not sure which screen" in text
