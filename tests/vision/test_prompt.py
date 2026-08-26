# tests/vision/test_prompt.py
from experiments.vision.prompt import build_vision_prompt
from experiments.vision.types import Message


def test_build_vision_prompt_basic():
    prompt = build_vision_prompt(
        partner_state="answering_qs",
        partner_message="look at this",
        conversation_history=[
            Message(role="concierge", content="Open the app and check the Home tab."),
            Message(role="partner", content="I don't see it"),
        ],
    )
    assert "answering_qs" in prompt
    assert "look at this" in prompt
    assert "I don't see it" in prompt
    assert "home_screen_default" in prompt  # taxonomy injected
    assert "is_app_screenshot" in prompt  # schema reference


def test_build_vision_prompt_no_message():
    prompt = build_vision_prompt(
        partner_state="outreach",
        partner_message=None,
        conversation_history=[],
    )
    assert "No text message" in prompt
    assert "outreach" in prompt


def test_build_vision_prompt_truncates_history():
    history = [Message(role="partner", content=f"msg {i}") for i in range(10)]
    prompt = build_vision_prompt(
        partner_state="answering_qs",
        partner_message="help",
        conversation_history=history,
    )
    # Should only include last 3 messages in the summary
    assert "msg 9" in prompt
    assert "msg 7" in prompt
    assert "msg 0" not in prompt
