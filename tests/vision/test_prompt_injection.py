# tests/vision/test_prompt_injection.py
import sys
import os

# Add repo root to path so we can import server.services.draft_service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from server.services.draft_service import assemble_prompt
from experiments.vision.preprocessor import VisionPreprocessor
from experiments.vision.mock_provider import MockVisionProvider
from experiments.vision.types import ImageAnalysis


def test_vision_block_injected_into_prompt():
    """Simulate the production pattern: vision analysis prepended to the prompt."""
    # 1. Run vision preprocessor
    provider = MockVisionProvider()
    preprocessor = VisionPreprocessor(provider=provider)
    vision_block = preprocessor.process(
        media=[{"url": "https://media.telnyx.com/test.png", "content_type": "image/png", "sha256": "abc", "size": 100}],
        partner_message="I sent you a pic",
        conversation_history=[],
        partner_state="answering_qs",
        download_fn=lambda url: b"\x89PNG",
    )

    # 2. Build the standard prompt
    messages = [
        {"direction": "outbound", "content": "Hi! Welcome to Shiftsmart.", "ts": "2026-05-21T10:00:00"},
        {"direction": "inbound", "content": "I sent you a pic", "ts": "2026-05-21T10:01:00"},
    ]
    base_prompt = assemble_prompt(messages, first_name="Test")

    # 3. Inject vision block (the production pattern)
    full_prompt = f"{vision_block}\n\n{base_prompt}" if vision_block else base_prompt

    # 4. Assert vision context is present in the final prompt
    assert "## Image Analysis" in full_prompt
    assert "home_screen_default" in full_prompt
    assert "HARD RULES" in full_prompt  # original prompt structure intact
    assert "Draft a reply" in full_prompt  # still ends with the drafting instruction


def test_vision_block_not_injected_when_no_images():
    """When no images, prompt is unchanged."""
    messages = [
        {"direction": "outbound", "content": "Hi! Welcome to Shiftsmart.", "ts": "2026-05-21T10:00:00"},
        {"direction": "inbound", "content": "Where is orientation?", "ts": "2026-05-21T10:01:00"},
    ]
    base_prompt = assemble_prompt(messages, first_name="Test")

    # No vision block
    assert "## Image Analysis" not in base_prompt
    assert "HARD RULES" in base_prompt


def test_vision_non_app_image_injects_deflect():
    """Non-app images get the deflect block."""
    provider = MockVisionProvider(is_app=False)
    preprocessor = VisionPreprocessor(provider=provider)
    vision_block = preprocessor.process(
        media=[{"url": "https://media.telnyx.com/selfie.jpg", "content_type": "image/jpeg", "sha256": "xyz", "size": 200}],
        partner_message=None,
        conversation_history=[],
        partner_state="answering_qs",
        download_fn=lambda url: b"\xff\xd8\xff",
    )

    messages = [
        {"direction": "outbound", "content": "Hi! Welcome.", "ts": "2026-05-21T10:00:00"},
        {"direction": "inbound", "content": "", "ts": "2026-05-21T10:01:00"},
    ]
    base_prompt = assemble_prompt(messages, first_name="Test")
    full_prompt = f"{vision_block}\n\n{base_prompt}" if vision_block else base_prompt

    assert "not a Shiftsmart app screenshot" in full_prompt
    assert "Respond to their text message normally" in full_prompt
