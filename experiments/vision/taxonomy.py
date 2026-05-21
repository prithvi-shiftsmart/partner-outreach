# experiments/vision/taxonomy.py
SCREEN_IDS: dict[str, str] = {
    "home_screen_default": "Home tab, normal state — no orientation card visible",
    "home_screen_with_orientation": "Home tab showing the In-app orientation card with $10 banner",
    "shifts_tab_empty": "Shifts tab selected, no shifts listed — empty state",
    "shifts_tab_with_shifts": "Shifts tab showing one or more shift cards",
    "shifts_tab_with_lock_icon": "Shifts tab showing a shift with a lock icon (orientation entry point)",
    "orientation_module_N": "Inside orientation, on a specific learning module (1-9)",
    "orientation_complete": "Orientation completion / congratulations screen",
    "payment_setup": "Stripe / payment method setup screen",
    "payment_error": "Payment setup showing an error message",
    "error_dialog": "Error popup or modal dialog over any screen",
    "login_screen": "Login or password entry screen",
    "banned_screen": "Account banned / disabled / deactivated message",
    "profile_screen": "Profile tab showing account details",
    "earnings_tab": "Earnings / payment history screen",
    "work_experience_screen": "Work experience input or search field",
    "bgc_screen": "Background check status or submission screen",
    "confirmation_call_screen": "Phone number verification / confirmation call step",
    "non_app_image": "Not a Shiftsmart app screenshot (selfie, meme, photo, document, etc.)",
    "unidentifiable": "Appears to be an app screenshot but screen cannot be determined",
}


def screen_id_description(screen_id: str) -> str:
    return SCREEN_IDS.get(screen_id, "Unknown screen")


def screen_ids_for_prompt() -> str:
    lines = [f"- {sid}: {desc}" for sid, desc in SCREEN_IDS.items()]
    return "\n".join(lines)
