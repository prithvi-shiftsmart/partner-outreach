# tests/vision/test_preprocessor.py
from experiments.vision.preprocessor import VisionPreprocessor
from experiments.vision.mock_provider import MockVisionProvider
from experiments.vision.types import Message, ImageAnalysis


def _make_media(
    content_type: str = "image/png",
    sha256: str = "abc123",
    url: str = "https://media.telnyx.com/test.png",
    size: int = 1024,
) -> dict:
    return {"url": url, "content_type": content_type, "sha256": sha256, "size": size}


def test_preprocessor_produces_context_block():
    provider = MockVisionProvider()
    preprocessor = VisionPreprocessor(provider=provider)
    result = preprocessor.process(
        media=[_make_media()],
        partner_message="look at this",
        conversation_history=[],
        partner_state="answering_qs",
        download_fn=lambda url: b"\x89PNG",
    )
    assert "## Image Analysis" in result
    assert "home_screen_default" in result


def test_preprocessor_skips_non_image_media():
    provider = MockVisionProvider()
    preprocessor = VisionPreprocessor(provider=provider)
    result = preprocessor.process(
        media=[{"url": "https://x.com/vid.mp4", "content_type": "video/mp4", "sha256": "v1", "size": 500}],
        partner_message="check this video",
        conversation_history=[],
        partner_state="answering_qs",
        download_fn=lambda url: b"video",
    )
    assert result is None


def test_preprocessor_deduplicates_by_sha256():
    call_count = 0
    original_fixture = MockVisionProvider()

    class CountingProvider(MockVisionProvider):
        def analyze(self, request):
            nonlocal call_count
            call_count += 1
            return super().analyze(request)

    preprocessor = VisionPreprocessor(provider=CountingProvider())
    result = preprocessor.process(
        media=[
            _make_media(sha256="same_hash"),
            _make_media(sha256="same_hash"),
            _make_media(sha256="different_hash"),
        ],
        partner_message=None,
        conversation_history=[],
        partner_state="answering_qs",
        download_fn=lambda url: b"\x89PNG",
    )
    # Provider called once with 2 unique images (not 3)
    assert call_count == 1
    assert "2 screenshot(s)" in result


def test_preprocessor_handles_download_failure():
    provider = MockVisionProvider()
    preprocessor = VisionPreprocessor(provider=provider)

    def failing_download(url: str) -> bytes:
        raise ConnectionError("404 Not Found")

    result = preprocessor.process(
        media=[_make_media()],
        partner_message="help",
        conversation_history=[],
        partner_state="answering_qs",
        download_fn=failing_download,
    )
    assert result is None


def test_preprocessor_handles_provider_error():
    class FailingProvider(MockVisionProvider):
        def analyze(self, request):
            raise TimeoutError("Vision model timed out")

    preprocessor = VisionPreprocessor(provider=FailingProvider())
    result = preprocessor.process(
        media=[_make_media()],
        partner_message="help",
        conversation_history=[],
        partner_state="answering_qs",
        download_fn=lambda url: b"\x89PNG",
    )
    assert result is None
