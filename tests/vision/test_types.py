# tests/vision/test_types.py
from experiments.vision.types import ImageData, Message, VisionRequest, ImageAnalysis


def test_image_data_creation():
    img = ImageData(content=b"\x89PNG", content_type="image/png", size=4, sha256="abc123")
    assert img.content_type == "image/png"
    assert img.size == 4


def test_image_data_rejects_non_image():
    import pytest
    with pytest.raises(ValueError, match="content_type must start with image/"):
        ImageData(content=b"data", content_type="video/mp4", size=4, sha256="abc")


def test_message_creation():
    msg = Message(role="partner", content="I can't find orientation")
    assert msg.role == "partner"


def test_vision_request_creation():
    img = ImageData(content=b"\x89PNG", content_type="image/png", size=4, sha256="abc")
    req = VisionRequest(
        images=[img],
        partner_message="look at this",
        conversation_history=[],
        partner_state="answering_qs",
    )
    assert len(req.images) == 1
    assert req.partner_state == "answering_qs"


def test_image_analysis_creation():
    analysis = ImageAnalysis(
        screen_id="shifts_tab_empty",
        visible_elements="Bottom nav: Home, Shifts (selected), Earnings, Profile",
        error_state=None,
        partner_problem="No shifts available in partner's area",
        suggested_action="Tell partner to check back daily",
        confidence=0.92,
        is_app_screenshot=True,
    )
    assert analysis.is_app_screenshot is True
    assert analysis.confidence == 0.92


def test_image_analysis_confidence_bounds():
    import pytest
    with pytest.raises(ValueError):
        ImageAnalysis(
            screen_id="test",
            visible_elements="test",
            error_state=None,
            partner_problem="test",
            suggested_action="test",
            confidence=1.5,
            is_app_screenshot=True,
        )
