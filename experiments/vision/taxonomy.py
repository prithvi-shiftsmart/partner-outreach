# experiments/vision/taxonomy.py
SCREEN_IDS: dict[str, str] = {
    # ── Pre-auth: Welcome & Signup ──────────────────────────────────────
    "welcome_splash": "Splash screen — Shiftsmart logo, tagline, client logos (Walmart, Circle K, Pepsi, Starbucks), Get Started CTA, blue gradient",
    "get_to_know": "Get to know Shiftsmart intro screen — partner photo, Continue CTA, blue gradient background",
    "signup_phone": "Phone number entry form — US flag, phone input, referral code link, SMS consent checkbox, Continue CTA",
    "verify_number": "SMS code verification — Verify your number header, code input, resend countdown, Use a different number link",
    "create_account": "Account creation form — first/last name, email, DOB, password fields with requirements checklist, Create Account CTA",

    # ── Post-auth: Profile Setup ────────────────────────────────────────
    "shift_categories": "Shift category overview — Food preparation and Shelf stocking cards with avg pay and shift counts, Continue CTA",
    "find_shifts": "Find shifts near you — map with store pins, location permission modal or resolved location with role cards",
    "attribution_survey": "How did you hear about Shiftsmart survey — single-select radio list, Submit CTA, blue gradient",
    "transportation_survey": "Transportation mode survey — How do you plan on getting to shifts, single-select radio list, Submit CTA",
    "work_experience_screen": "Work experience input — search for a company field, typeahead results, or role/duration selection modals",
    "profile_photo": "Profile photo upload prompt — circular avatar placeholder, Add Photo CTA, Skip for now link, blue gradient",
    "review_policies": "Policy review — contractor agreement, cancellation policy, anti-fraud policy cards with Learn more links, Accept Terms CTA",

    # ── Post-onboarding: Main App (first session) ──────────────────────
    "home_screen_default": "Home tab, normal state — no orientation card visible",
    "home_screen_with_orientation": "Home tab showing the In-app orientation card — REQUIRED TO UNLOCK SHIFTS banner, 4 steps, ~50 min, $10 + 100 pts, Get started link",
    "home_tab_payment_prompt": "Home tab scrolled to payment setup — Up Next: Add payment method section with green callout, locked shift card above",
    "shifts_tab_empty": "Shifts tab selected, no shifts listed — empty state",
    "shifts_tab_with_shifts": "Shifts tab showing one or more unlocked shift cards",
    "shifts_tab_with_lock_icon": "Shifts tab showing a shift with a lock icon (orientation entry point)",
    "shifts_tab_locked": "Shifts tab pre-orientation — day selector, filter pills, multiple locked shift cards with Unlock this shift labels",
    "earnings_tab": "Earnings tab — Funds/Shift History/Bonuses tabs, balance card, recently withdrawn section",
    "earnings_tab_no_payout": "Earnings tab with Missing Payout Method red alert banner — Add a bank or card link, $0 available balance",
    "profile_tab": "Profile tab — user photo, name, Shiftsmart Partner subtitle, Promos section, My Profile section with Personal Details and Projects",
    "profile_screen": "Profile tab showing account details",

    # ── Orientation ─────────────────────────────────────────────────────
    "orientation_module_list": "Orientation module list — active module card with Not Started badge, remaining modules as locked rows with duration and Locked pill, Need help pill",
    "orientation_module_detail": "Orientation module detail — module icon, duration, section list (video/guided tutorial/solo practice), Start CTA with progress bar",
    "orientation_module_N": "Inside orientation, on a specific learning module (1-9)",
    "orientation_complete": "Orientation completion / congratulations screen",

    # ── Payment & Errors ────────────────────────────────────────────────
    "payment_setup": "Stripe / payment method setup screen",
    "payment_error": "Payment setup showing an error message",
    "error_dialog": "Error popup or modal dialog over any screen",

    # ── Auth & Account ──────────────────────────────────────────────────
    "login_screen": "Login or password entry screen",
    "banned_screen": "Account banned / disabled / deactivated message",
    "bgc_screen": "Background check status or submission screen",
    "confirmation_call_screen": "Phone number verification / confirmation call step",

    # ── Catch-all ───────────────────────────────────────────────────────
    "non_app_image": "Not a Shiftsmart app screenshot (selfie, meme, photo, document, etc.)",
    "unidentifiable": "Appears to be an app screenshot but screen cannot be determined",
}


def screen_id_description(screen_id: str) -> str:
    return SCREEN_IDS.get(screen_id, "Unknown screen")


def screen_ids_for_prompt() -> str:
    lines = [f"- {sid}: {desc}" for sid, desc in SCREEN_IDS.items()]
    return "\n".join(lines)
