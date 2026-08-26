# experiments/vision/claude_provider.py
from __future__ import annotations

import base64
import json
import logging
import subprocess
import tempfile
import os

from experiments.vision.prompt import build_vision_prompt
from experiments.vision.provider import VisionProvider
from experiments.vision.types import ImageAnalysis, VisionRequest

logger = logging.getLogger(__name__)

CLAUDE_CLI = os.environ.get("CLAUDE_CLI_PATH", "claude")


class ClaudeVisionProvider(VisionProvider):
    def __init__(self, model: str = "sonnet", timeout: int = 30):
        self._model = model
        self._timeout = timeout

    def analyze(self, request: VisionRequest) -> ImageAnalysis:
        prompt_text = build_vision_prompt(
            partner_state=request.partner_state,
            partner_message=request.partner_message,
            conversation_history=request.conversation_history,
        )

        image_args = []
        temp_files = []
        try:
            for img in request.images:
                suffix = _extension_for(img.content_type)
                tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
                tmp.write(img.content)
                tmp.close()
                temp_files.append(tmp.name)
                image_args.extend(["--file", tmp.name])

            result = subprocess.run(
                [CLAUDE_CLI, "-p", "--model", self._model, "--output-format", "json", *image_args],
                input=prompt_text,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )

            if result.returncode != 0:
                logger.error("Claude CLI failed: %s", result.stderr)
                raise RuntimeError(f"Claude CLI exit code {result.returncode}")

            response = json.loads(result.stdout)
            text = response.get("result", result.stdout)

            # Extract JSON from response — handle markdown code fences
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                text = text.rsplit("```", 1)[0]
            text = text.strip()

            data = json.loads(text)
            return ImageAnalysis(**data)

        finally:
            for path in temp_files:
                try:
                    os.unlink(path)
                except OSError:
                    pass


def _extension_for(content_type: str) -> str:
    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/bmp": ".bmp",
        "image/tiff": ".tiff",
    }
    return mapping.get(content_type, ".png")
