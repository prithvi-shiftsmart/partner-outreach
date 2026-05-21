# tests/vision/conftest.py
import os
import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "vision")
IMAGES_DIR = os.path.join(FIXTURES_DIR, "images")


@pytest.fixture
def images_dir():
    return IMAGES_DIR


@pytest.fixture
def load_image():
    def _load(filename: str) -> bytes:
        path = os.path.join(IMAGES_DIR, filename)
        with open(path, "rb") as f:
            return f.read()
    return _load
