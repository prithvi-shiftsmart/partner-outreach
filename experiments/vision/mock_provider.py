# experiments/vision/mock_provider.py
from __future__ import annotations

from experiments.vision.provider import VisionProvider
from experiments.vision.types import ImageAnalysis, VisionRequest


class MockVisionProvider(VisionProvider):
    def __init__(
        self,
        fixture: ImageAnalysis | None = None,
        is_app: bool = True,
        screen_id: str | None = None,
        problem: str | None = None,
        action: str | None = None,
        confidence: float = 0.88,
    ):
        self._fixture = fixture
        self._is_app = is_app
        self._screen_id = screen_id
        self._problem = problem
        self._action = action
        self._confidence = confidence

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

        sid = self._screen_id or "home_screen_default"
        problem = self._problem or "Partner cannot find orientation entry point on Home screen"
        action = self._action or "Guide to Shifts tab lock-icon fallback"

        return ImageAnalysis(
            screen_id=sid,
            visible_elements="Bottom nav: Home (selected), Shifts, Earnings, Profile.",
            error_state=None,
            partner_problem=problem,
            suggested_action=action,
            confidence=self._confidence,
            is_app_screenshot=True,
        )
