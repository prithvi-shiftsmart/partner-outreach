# tests/vision/test_taxonomy.py
from experiments.vision.taxonomy import SCREEN_IDS, screen_id_description, screen_ids_for_prompt


def test_screen_ids_contains_required_keys():
    required = [
        "home_screen_default", "shifts_tab_empty", "shifts_tab_with_shifts",
        "orientation_complete", "error_dialog", "login_screen", "banned_screen",
        "work_experience_screen", "non_app_image", "unidentifiable",
    ]
    for key in required:
        assert key in SCREEN_IDS, f"Missing required screen ID: {key}"


def test_screen_id_description():
    desc = screen_id_description("shifts_tab_empty")
    assert "Shifts tab" in desc


def test_screen_id_description_unknown():
    desc = screen_id_description("totally_fake_id")
    assert desc == "Unknown screen"


def test_screen_ids_for_prompt():
    prompt_text = screen_ids_for_prompt()
    assert "home_screen_default" in prompt_text
    assert "non_app_image" in prompt_text
    assert "\n" in prompt_text
