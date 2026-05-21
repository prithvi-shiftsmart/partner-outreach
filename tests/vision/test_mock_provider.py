# tests/vision/test_mock_provider.py
import pytest
from experiments.vision.types import ImageData, VisionRequest, Message, ImageAnalysis
from experiments.vision.mock_provider import MockVisionProvider
from experiments.vision.provider import VisionProvider


def _make_image(content_type: str = "image/png", sha256: str = "abc") -> ImageData:
    return ImageData(content=b"\x89PNG", content_type=content_type, size=4, sha256=sha256)


def test_mock_provider_is_a_vision_provider():
    provider = MockVisionProvider()
    assert isinstance(provider, VisionProvider)


def test_mock_provider_returns_default_analysis():
    provider = MockVisionProvider()
    req = VisionRequest(
        images=[_make_image()],
        partner_message="look at this",
        conversation_history=[],
        partner_state="answering_qs",
    )
    result = provider.analyze(req)
    assert isinstance(result, ImageAnalysis)
    assert result.is_app_screenshot is True
    assert result.confidence > 0


def test_mock_provider_returns_custom_fixture():
    fixture = ImageAnalysis(
        screen_id="banned_screen",
        visible_elements="Account banned message",
        error_state="Your account has been deactivated",
        partner_problem="Partner is banned",
        suggested_action="Direct to support@shiftsmart.com",
        confidence=0.95,
        is_app_screenshot=True,
    )
    provider = MockVisionProvider(fixture=fixture)
    req = VisionRequest(
        images=[_make_image()],
        partner_message=None,
        conversation_history=[],
        partner_state="answering_qs",
    )
    result = provider.analyze(req)
    assert result.screen_id == "banned_screen"
    assert result.error_state == "Your account has been deactivated"


def test_mock_provider_non_app_image():
    provider = MockVisionProvider(is_app=False)
    req = VisionRequest(
        images=[_make_image()],
        partner_message="check this out",
        conversation_history=[],
        partner_state="outreach",
    )
    result = provider.analyze(req)
    assert result.is_app_screenshot is False
    assert result.screen_id == "non_app_image"
