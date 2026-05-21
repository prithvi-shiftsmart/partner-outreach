# experiments/vision/preprocessor.py
from __future__ import annotations

import logging
from typing import Callable

from experiments.vision.format import format_analysis_for_prompt
from experiments.vision.provider import VisionProvider
from experiments.vision.types import ImageData, Message, VisionRequest

logger = logging.getLogger(__name__)


class VisionPreprocessor:
    def __init__(self, provider: VisionProvider):
        self._provider = provider

    def process(
        self,
        media: list[dict],
        partner_message: str | None,
        conversation_history: list[Message | dict],
        partner_state: str,
        download_fn: Callable[[str], bytes],
    ) -> str | None:
        images = self._download_and_filter(media, download_fn)
        if not images:
            return None

        history = [
            m if isinstance(m, Message) else Message(**m)
            for m in conversation_history
        ]

        request = VisionRequest(
            images=images,
            partner_message=partner_message,
            conversation_history=history,
            partner_state=partner_state,
        )

        try:
            analysis = self._provider.analyze(request)
        except Exception:
            logger.exception("Vision provider failed")
            return None

        return format_analysis_for_prompt(analysis, image_count=len(images))

    def _download_and_filter(
        self,
        media: list[dict],
        download_fn: Callable[[str], bytes],
    ) -> list[ImageData]:
        seen_hashes: set[str] = set()
        images: list[ImageData] = []

        for item in media:
            if not item.get("content_type", "").startswith("image/"):
                continue

            sha = item.get("sha256", "")
            if sha in seen_hashes:
                continue
            seen_hashes.add(sha)

            try:
                content = download_fn(item["url"])
            except Exception:
                logger.warning("Failed to download %s", item["url"])
                continue

            images.append(ImageData(
                content=content,
                content_type=item["content_type"],
                size=item.get("size", len(content)),
                sha256=sha,
            ))

        return images
