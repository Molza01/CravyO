from datetime import datetime, timezone
from typing import TypedDict


class MealWindow(TypedDict):
    name: str
    start_hour: int
    end_hour: int
    prep_buffer_mins: int
    label: str
    nudge_message: str


MEAL_WINDOWS: list[MealWindow] = [
    MealWindow(
        name="breakfast",
        start_hour=7,
        end_hour=10,
        prep_buffer_mins=30,
        label="Breakfast",
        nudge_message="Rise and shine! Your morning craving awaits.",
    ),
    MealWindow(
        name="lunch",
        start_hour=12,
        end_hour=14,
        prep_buffer_mins=45,
        label="Lunch",
        nudge_message="Lunch window is open. Time to satisfy that craving!",
    ),
    MealWindow(
        name="evening_snacks",
        start_hour=17,
        end_hour=19,
        prep_buffer_mins=30,
        label="Evening Snacks",
        nudge_message="Snack time! Quick delivery options are available.",
    ),
    MealWindow(
        name="dinner",
        start_hour=19,
        end_hour=22,
        prep_buffer_mins=60,
        label="Dinner",
        nudge_message="Dinner time! Order now to eat at your ideal time.",
    ),
    MealWindow(
        name="late_night",
        start_hour=22,
        end_hour=23,
        prep_buffer_mins=20,
        label="Late Night",
        nudge_message="Late night cravings? Quick delivery spots are open.",
    ),
]


def _current_window() -> MealWindow | None:
    now = datetime.now(timezone.utc)
    hour = now.hour
    for window in MEAL_WINDOWS:
        if window["start_hour"] <= hour < window["end_hour"]:
            return window
    return None


def _minutes_until(window_name: str) -> int:
    now = datetime.now(timezone.utc)
    current_hour = now.hour
    current_min = now.minute
    w = next((m for m in MEAL_WINDOWS if m["name"] == window_name), None)
    if not w:
        return 999
    start = w["start_hour"]
    if current_hour < start:
        return (start - current_hour) * 60 - current_min
    if current_hour >= start:
        next_day_start = start + 24
        return (next_day_start - current_hour) * 60 - current_min
    return 0


def _urgency_from_minutes(mins: int) -> str:
    if mins <= 5:
        return "critical"
    if mins <= 15:
        return "high"
    if mins <= 30:
        return "medium"
    return "low"


class NudgeResult(TypedDict):
    message: str
    urgency: str
    meal_window: str
    countdown_mins: int
    prep_buffer_mins: int
    order_now: bool
    pre_window: bool


def get_meal_nudge(
    fused_dish: str,
    fused_cuisine: str,
    urgency_override: str | None = None,
) -> NudgeResult:
    now = datetime.now(timezone.utc)
    hour = now.hour
    current_window = _current_window()

    if current_window:
        label = current_window["label"]
        nudge = current_window["nudge_message"]
        prep = current_window["prep_buffer_mins"]
        countdown = 0
        pre_window = False

        if fused_dish:
            message = f"[{label}] {nudge} '{fused_dish}' detected — ready to order?"
        else:
            message = f"[{label}] {nudge}"

        urgency = urgency_override or "medium"
        if urgency_override in ("critical", "high", "medium", "low"):
            urgency = urgency_override
        elif hour >= current_window["end_hour"] - 1:
            urgency = "high"
        else:
            urgency = "medium"

        return NudgeResult(
            message=message,
            urgency=urgency,
            meal_window=current_window["name"],
            countdown_mins=countdown,
            prep_buffer_mins=prep,
            order_now=True,
            pre_window=False,
        )

    future_windows = [w for w in MEAL_WINDOWS if w["start_hour"] > hour]
    if not future_windows:
        next_window = next(
            (w for w in MEAL_WINDOWS if w["name"] == "breakfast"), MEAL_WINDOWS[0]
        )
    else:
        next_window = future_windows[0]

    countdown = _minutes_until(next_window["name"])
    urgency_raw = _urgency_from_minutes(countdown)
    urgency = urgency_override or urgency_raw

    pre_window = True
    order_now = False

    if fused_dish:
        if next_window["name"] == "breakfast":
            message = (
                f"Good morning! '{fused_dish}' is on deck for breakfast. "
                f"Order in {countdown} mins to have it ready on time."
            )
        elif next_window["name"] == "lunch":
            message = (
                f"'{fused_dish}' for lunch? Window opens in {countdown} mins — "
                f"set a reminder or order ahead!"
            )
        elif next_window["name"] == "evening_snacks":
            message = (
                f"'{fused_dish}' craving? Snack time in {countdown} mins. "
                f"Quick delivery available!"
            )
        elif next_window["name"] == "dinner":
            message = (
                f"'{fused_dish}' for dinner? Order in {countdown} mins "
                f"to arrive by mealtime."
            )
        else:
            message = (
                f"'{fused_dish}' craving detected. "
                f"Window opens in {countdown} mins — we'll notify you!"
            )
    else:
        message = f"Next meal window: {next_window['label']} in {countdown} mins."

    return NudgeResult(
        message=message,
        urgency=urgency,
        meal_window=next_window["name"],
        countdown_mins=countdown,
        prep_buffer_mins=next_window["prep_buffer_mins"],
        order_now=order_now,
        pre_window=pre_window,
    )


def build_countdown_nudge(fused_dish: str, window_name: str, mins_remaining: int) -> str:
    if mins_remaining <= 5:
        return f"Order '{fused_dish}' now — window closing in {mins_remaining} mins!"
    if mins_remaining <= 15:
        return (
            f"'{fused_dish}' window closes in {mins_remaining} mins. "
            f"Quick, order now for delivery in time!"
        )
    return (
        f"'{fused_dish}' — {mins_remaining} mins until your {window_name} window. "
        f"Stay tuned!"
    )