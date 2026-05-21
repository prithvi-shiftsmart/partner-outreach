# experiments/vision/mock_provider.py
from __future__ import annotations

from experiments.vision.provider import VisionProvider
from experiments.vision.types import ImageAnalysis, VisionRequest


class MockVisionProvider(VisionProvider):
    def __init__(
        self,
        fixture: ImageAnalysis | None = None,
        is_app: bool = True,
    ):
        self._fixture = fixture
        self._is_app = is_app

    def analyze(self, request: VisionRequest) -> ImageAnalysis:
        if self._fixture is not None:
            return self._fixture

        if not self._is_app:
            return ImageAnalysis(
                screen_id="non_app_image",
                visible_elements="Non-app content",
                error_state=None,
                partner_problem="Image is not a Shiftsmart app screenshot",
                suggested_action="Respond to text message normally",
                confidence=0.85,
                is_app_screenshot=False,
            )

        return ImageAnalysis(
            screen_id="home_screen_default",
            visible_elements="Bottom nav: Home (selected), Shifts, Earnings, Profile. No orientation card visible.",
            error_state=None,
            partner_problem="Partner cannot find orientation entry point on Home screen",
            suggested_action="Guide to Shifts tab lock-icon fallback",
            confidence=0.88,
            is_app_screenshot=True,
        )
