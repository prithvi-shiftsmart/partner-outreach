# experiments/vision/provider.py
from __future__ import annotations

from abc import ABC, abstractmethod

from experiments.vision.types import ImageAnalysis, VisionRequest


class VisionProvider(ABC):
    @abstractmethod
    def analyze(self, request: VisionRequest) -> ImageAnalysis:
        """Analyze images and return structured screen analysis."""
        ...
