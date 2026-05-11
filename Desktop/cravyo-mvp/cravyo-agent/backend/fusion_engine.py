from datetime import datetime, timezone
from typing import TypedDict


class PlatformCraving(TypedDict):
    platform: str
    food: str
    confidence: float
    detected_at: str
    frequency: int
    recency_weight: float
    final_score: float


class FusionResult(TypedDict):
    fused_dish: str
    fused_cuisine: str
    platform_cravings: list[PlatformCraving]
    recommended_combo: str | None
    reasoning: str
    urgency: str
    meal_window: str
    time_until_window: int


_PLATFORM_WEIGHTS = {
    "instagram": 0.35,
    "youtube": 0.30,
    "twitter": 0.15,
    "reddit": 0.10,
    "facebook": 0.05,
    "tiktok": 0.05,
}

_RECENCY_HALF_LIFE_HOURS = 48
_MAX_FREQUENCY = 5


def _recency_weight(detected_at: str) -> float:
    try:
        detected = datetime.fromisoformat(detected_at.replace("Z", "+00:00"))
    except Exception:
        return 0.3
    now = datetime.now(timezone.utc)
    age_hours = (now - detected).total_seconds() / 3600
    return max(0.1, 1.0 - (age_hours / _RECENCY_HALF_LIFE_HOURS))


def _compute_score(
    platform: str,
    confidence: float,
    frequency: int,
    recency_weight: float,
) -> float:
    pw = _PLATFORM_WEIGHTS.get(platform.lower(), 0.10)
    freq_bonus = min(frequency / _MAX_FREQUENCY, 1.0) * 0.1
    return round((pw * confidence * 0.6) + (pw * freq_bonus * 0.2) + (recency_weight * 0.2), 4)


def _infer_cuisine(food: str) -> str:
    cuisine_map = {
        "biryani": "indian", "butter chicken": "indian", "paneer": "indian",
        "naan": "indian", "dal": "indian", "samosa": "indian",
        "pizza": "italian", "pasta": "italian", "risotto": "italian",
        "burger": "american", "hotdog": "american", " BBQ": "american",
        "sushi": "japanese", "ramen": "japanese", "miso": "japanese",
        "noodles": "chinese", "manchurian": "chinese", "dim sum": "chinese",
        "taco": "mexican", "burrito": "mexican", "quesadilla": "mexican",
        "salad": "healthy", "smoothie": "healthy", "acai": "healthy",
        "pancake": "breakfast", "waffle": "breakfast", "french toast": "breakfast",
        "ice cream": "dessert", "brownie": "dessert", "cheesecake": "dessert",
        "coffee": "beverage", "tea": "beverage", "frappe": "beverage",
        "chips": "snack", "samosa": "snack", " chaat": "snack",
    }
    food_lower = food.lower()
    for item, cuisine in cuisine_map.items():
        if item in food_lower:
            return cuisine
    return "universal"


def _same_cuisine(a: str, b: str) -> bool:
    return _infer_cuisine(a) == _infer_cuisine(b)


def _complementary(a: str, b: str) -> bool:
    pairs = {
        ("biryani", "butter chicken"), ("butter chicken", "biryani"),
        ("pizza", "pasta"), ("pasta", "pizza"),
        ("burger", "fries"), ("fries", "burger"),
        ("sushi", "ramen"), ("ramen", "sushi"),
        ("noodles", "manchurian"), ("manchurian", "noodles"),
        ("taco", "burrito"), ("burrito", "taco"),
    }
    return (a.lower(), b.lower()) in pairs or (b.lower(), a.lower()) in pairs


def fusion_engine(cravings: list[dict]) -> FusionResult:
    if not cravings:
        return FusionResult(
            fused_dish="",
            fused_cuisine="",
            platform_cravings=[],
            recommended_combo=None,
            reasoning="No cravings provided.",
            urgency="low",
            meal_window="snacks",
            time_until_window=0,
        )

    scored: list[PlatformCraving] = []
    for c in cravings:
        dt = c.get("detected_at", datetime.now(timezone.utc).isoformat())
        rw = _recency_weight(dt)
        raw_platform = c.get("platform", "unknown")
        raw_confidence = float(c.get("confidence", 0.5))
        raw_frequency = int(c.get("frequency", 1))
        score = _compute_score(raw_platform, raw_confidence, raw_frequency, rw)
        scored.append(PlatformCraving(
            platform=raw_platform,
            food=c.get("food", c.get("dish", "")),
            confidence=raw_confidence,
            detected_at=dt,
            frequency=raw_frequency,
            recency_weight=round(rw, 4),
            final_score=score,
        ))

    scored.sort(key=lambda x: x["final_score"], reverse=True)

    top = scored[0]
    fused_dish = top["food"]
    fused_cuisine = _infer_cuisine(fused_dish)

    recommended_combo: str | None = None
    reasoning = f"'{fused_dish}' scored highest ({top['final_score']}) from {top['platform']}."

    if len(scored) >= 2:
        second = scored[1]
        if _same_cuisine(fused_dish, second["food"]):
            combo = f"{fused_dish} + {second['food']}"
            recommended_combo = combo
            reasoning += f" '{second['food']}' shares the same cuisine — suggesting combo platter."
        elif _complementary(fused_dish, second["food"]):
            combo = f"{fused_dish} combo with {second['food']}"
            recommended_combo = combo
            reasoning += f" '{second['food']}' is a natural pairing — suggesting combo."
        else:
            reasoning += f" '{second['food']}' ({second['platform']}) differs; multi-cuisine variety detected."

    top_platform = top["platform"]
    confidence_avg = sum(s["confidence"] for s in scored) / len(scored)
    if confidence_avg > 0.75 and top["final_score"] > 0.4:
        urgency = "high"
    elif confidence_avg > 0.5 or top["final_score"] > 0.25:
        urgency = "medium"
    else:
        urgency = "low"

    window, time_until = _meal_window_estimate()
    urgency = _adjust_urgency_by_timing(urgency, window, time_until)

    return FusionResult(
        fused_dish=fused_dish,
        fused_cuisine=fused_cuisine,
        platform_cravings=scored,
        recommended_combo=recommended_combo,
        reasoning=reasoning,
        urgency=urgency,
        meal_window=window,
        time_until_window=time_until,
    )


def _meal_window_estimate() -> tuple[str, int]:
    now = datetime.now(timezone.utc)
    hour = now.hour

    windows = [
        ("breakfast", 7, 10, 30),
        ("lunch", 12, 14, 60),
        ("evening_snacks", 17, 19, 60),
        ("dinner", 19, 22, 90),
        ("late_night", 22, 23, 60),
    ]

    for name, start, end, prep in windows:
        if start <= hour < end:
            return name, 0

    if hour < 7:
        return "breakfast", (7 - hour) * 60
    elif hour < 12:
        return "lunch", (12 - hour) * 60
    elif hour < 17:
        return "evening_snacks", (17 - hour) * 60
    elif hour < 19:
        return "dinner", (19 - hour) * 60
    elif hour < 22:
        return "late_night", (22 - hour) * 60
    else:
        return "breakfast", ((24 - hour) + 7) * 60


def _adjust_urgency_by_timing(urgency: str, window: str, time_until: int) -> str:
    if time_until == 0 and urgency in ("medium", "high"):
        return "critical"
    if window == "late_night" and time_until < 30:
        return "high"
    return urgency