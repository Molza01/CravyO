"""
Swiggy Service — Mock Implementation
Returns realistic mock data for demo/MVP use.
Replace with real Swiggy API calls when available.
"""

import random
from typing import Optional

# ── Restaurant catalogue ───────────────────────────────────────────────────────
RESTAURANT_DATA = {
    "indian": [
        {"name": "Behrouz Biryani",    "rating": 4.5, "delivery_time": "35-45 min", "delivery_fee": 30, "price_range": "₹300-600", "tags": ["biryani", "mughlai"]},
        {"name": "Paradise Biryani",   "rating": 4.3, "delivery_time": "30-40 min", "delivery_fee": 25, "price_range": "₹250-500", "tags": ["biryani", "south-indian"]},
        {"name": "Haldiram's",         "rating": 4.2, "delivery_time": "25-35 min", "delivery_fee": 20, "price_range": "₹150-400", "tags": ["snacks", "sweets", "thali"]},
        {"name": "Barbeque Nation",    "rating": 4.6, "delivery_time": "45-55 min", "delivery_fee": 35, "price_range": "₹500-900", "tags": ["grill", "bbq", "dineout"]},
        {"name": "Punjab Grill",       "rating": 4.4, "delivery_time": "35-45 min", "delivery_fee": 30, "price_range": "₹400-750", "tags": ["dal makhani", "paneer", "north-indian"]},
    ],
    "chinese": [
        {"name": "Yo! China",          "rating": 4.1, "delivery_time": "30-40 min", "delivery_fee": 25, "price_range": "₹300-550", "tags": ["noodles", "dim sum"]},
        {"name": "China Bistro",       "rating": 4.3, "delivery_time": "35-45 min", "delivery_fee": 30, "price_range": "₹350-600", "tags": ["hakka", "manchurian"]},
        {"name": "Dragon Bowl",        "rating": 4.0, "delivery_time": "25-35 min", "delivery_fee": 20, "price_range": "₹250-450", "tags": ["quick", "noodles"]},
    ],
    "italian": [
        {"name": "Domino's Pizza",     "rating": 4.2, "delivery_time": "25-35 min", "delivery_fee": 20, "price_range": "₹300-700", "tags": ["pizza", "pasta"]},
        {"name": "Pizza Hut",          "rating": 4.0, "delivery_time": "30-40 min", "delivery_fee": 25, "price_range": "₹350-750", "tags": ["pizza"]},
        {"name": "La Piazza",          "rating": 4.5, "delivery_time": "40-50 min", "delivery_fee": 40, "price_range": "₹500-900", "tags": ["fine-dining", "pasta", "risotto"]},
    ],
    "desserts": [
        {"name": "Baskin Robbins",     "rating": 4.3, "delivery_time": "20-30 min", "delivery_fee": 15, "price_range": "₹150-450", "tags": ["ice cream", "sundae"]},
        {"name": "Theobroma",          "rating": 4.6, "delivery_time": "35-45 min", "delivery_fee": 30, "price_range": "₹200-500", "tags": ["cheesecake", "brownies", "chocolate"]},
        {"name": "The Chocolate Room", "rating": 4.4, "delivery_time": "30-40 min", "delivery_fee": 25, "price_range": "₹200-550", "tags": ["chocolate", "waffles", "fondue"]},
        {"name": "Keventers",          "rating": 4.2, "delivery_time": "20-30 min", "delivery_fee": 15, "price_range": "₹150-350", "tags": ["milkshakes", "smoothies"]},
    ],
    "american": [
        {"name": "McDonald's",         "rating": 4.1, "delivery_time": "20-30 min", "delivery_fee": 20, "price_range": "₹200-500", "tags": ["burger", "fries"]},
        {"name": "Burger King",        "rating": 4.0, "delivery_time": "25-35 min", "delivery_fee": 20, "price_range": "₹200-450", "tags": ["burger", "whopper"]},
        {"name": "KFC",                "rating": 4.2, "delivery_time": "25-35 min", "delivery_fee": 25, "price_range": "₹250-500", "tags": ["fried chicken", "wings"]},
    ],
    "thai": [
        {"name": "Thai Orchid",        "rating": 4.4, "delivery_time": "40-50 min", "delivery_fee": 35, "price_range": "₹400-800", "tags": ["curry", "pad thai"]},
        {"name": "Asia Kitchen",       "rating": 4.2, "delivery_time": "35-45 min", "delivery_fee": 30, "price_range": "₹350-700", "tags": ["pan-asian"]},
    ],
    "mexican": [
        {"name": "Chipotle",           "rating": 4.2, "delivery_time": "30-40 min", "delivery_fee": 25, "price_range": "₹300-600", "tags": ["burrito", "bowl"]},
        {"name": "Taco Bell",          "rating": 4.0, "delivery_time": "25-35 min", "delivery_fee": 20, "price_range": "₹200-500", "tags": ["tacos", "quesadilla"]},
    ],
    "healthy": [
        {"name": "Eat Fit",            "rating": 4.3, "delivery_time": "30-40 min", "delivery_fee": 25, "price_range": "₹250-550", "tags": ["salads", "bowls", "low-calorie"]},
        {"name": "Green Bowl",         "rating": 4.5, "delivery_time": "25-35 min", "delivery_fee": 20, "price_range": "₹300-600", "tags": ["protein bowl", "smoothie"]},
        {"name": "Nourish Health Food","rating": 4.2, "delivery_time": "35-45 min", "delivery_fee": 30, "price_range": "₹300-650", "tags": ["detox", "whole grain"]},
    ],
}

# ── Instamart catalogue  ───────────────────────────────────────────────────────
# Each item: (name, price_inr)
INSTAMART_ITEMS: dict[str, list[tuple[str, int]]] = {
    "smoothie": [
        ("Raw Pressery Smoothie 250ml",       99),
        ("Epigamia Greek Yogurt 400g",        120),
        ("Tropicana Mixed Fruit 1L",          105),
        ("Nature's Basket Frozen Berries 300g", 180),
        ("Almond Breeze Almond Milk 1L",      140),
    ],
    "chocolate": [
        ("Cadbury Dairy Milk 200g",           90),
        ("Oreo Double Stuff 157g",            75),
        ("KitKat Chocolate 100g",             55),
        ("Ferrero Rocher 8-pack",             195),
        ("Cadbury Bournville 80g",            65),
    ],
    "desserts": [
        ("Amul Ice Cream Tub 500ml",          129),
        ("Theobroma Brownie 100g",            85),
        ("Oreo Original 300g",                65),
        ("Cadbury Dairy Milk 200g",           90),
        ("Baskin Robbins Pre-pack 125ml",     75),
    ],
    "snack": [
        ("Lay's Classic 130g",                35),
        ("Bingo Mad Angles 90g",              30),
        ("Kurkure Masala Munch 90g",          25),
        ("Haldiram's Aloo Bhujia 400g",       85),
        ("Too Yumm! Rice Crackers 60g",       25),
    ],
    "healthy": [
        ("Yoga Bar Protein Oats 400g",        199),
        ("Epigamia Greek Yogurt 400g",        120),
        ("Slurrp Farm Millet Muesli 400g",    285),
        ("The Whole Truth Protein Bar",        75),
        ("Sorich Dry Fruits Mix 200g",        199),
    ],
    "indian": [
        ("MDH Biryani Masala 100g",            55),
        ("Kohinoor Basmati Rice 1kg",          99),
        ("Mother Dairy Paneer 200g",           90),
        ("MTR Ready-to-Eat Dal Makhani",       85),
        ("Catch Spices Starter Kit",          165),
    ],
    "chinese": [
        ("Ching's Secret Hakka Noodles 240g",  55),
        ("Lee Kum Kee Soy Sauce 250ml",        95),
        ("ITC Master Chef Stir Fry Sauce",      95),
        ("Wai Wai Quick Noodles 75g",          18),
    ],
    "italian": [
        ("DiCasa Penne Pasta 500g",            65),
        ("Borges Olive Oil 250ml",            220),
        ("Kraft Parmesan Cheese 60g",          140),
        ("Del Monte Pasta Sauce 400g",         110),
    ],
    "default": [
        ("Maggi Noodles 560g",                 80),
        ("Assorted Biscuits Pack",             60),
        ("Tropicana Orange Juice 1L",          99),
        ("Amul Butter 500g",                  265),
    ],
}


# ── Smart item picker ──────────────────────────────────────────────────────────

def _pick_instamart_category(
    cuisine: str,
    specific_foods: list[str],
    is_snack: bool,
    dietary: str,
) -> str:
    """Return the INSTAMART_ITEMS key that best matches the detected cravings."""
    food_text = " ".join(specific_foods).lower()

    # Most-specific matches first
    if any(w in food_text for w in ["smoothie", "juice", "shake", "yogurt", "milkshake"]):
        return "smoothie"
    if any(w in food_text for w in ["chocolate", "brownie", "oreo", "kitkat", "cocoa"]):
        return "chocolate"
    if any(w in food_text for w in ["ice cream", "cheesecake", "cake", "pastry", "dessert", "waffle", "tiramisu"]):
        return "desserts"
    if dietary in ("gym", "diet") or any(w in food_text for w in ["protein", "oats", "muesli", "granola", "quinoa"]):
        return "healthy"
    if is_snack or any(w in food_text for w in ["chips", "biscuit", "cookie", "popcorn", "wafer", "snack", "crackers"]):
        return "snack"

    # Cuisine fallback
    return cuisine if cuisine in INSTAMART_ITEMS else "default"


# ── Formatting helpers ─────────────────────────────────────────────────────────

_LINE = "─" * 57

def _mini_table(items: list[tuple[str, int]], label: str) -> str:
    """Render a compact shopping-list table."""
    lines = [
        f"  {_LINE}",
        f"  {'Item':<40} {'Price':>8}",
        f"  {_LINE}",
    ]
    total = 0
    for name, price in items:
        lines.append(f"  {name:<40} {'₹' + str(price):>8}")
        total += price
    delivery = 0  # Instamart free above ₹199
    lines += [
        f"  {_LINE}",
        f"  {'+ Delivery fee':<40} {'Free':>8}" if total >= 199 else
        f"  {'+ Delivery fee':<40} {'₹25':>8}",
        f"  {'Estimated Total':<40} {'₹' + str(total + (0 if total >= 199 else 25)):>8}",
        f"  {_LINE}",
    ]
    return "\n".join(lines)


def _restaurant_table(restaurants: list[dict], mode: str) -> str:
    """Render a clean restaurant listing."""
    lines = [
        f"  {_LINE}",
        f"  {'Restaurant':<24} {'Rating':>6} {'Time':>12} {'Price Range':>14}",
        f"  {_LINE}",
    ]
    for r in restaurants:
        stars = f"{r['rating']}★"
        time_ = r["delivery_time"] if mode != "dineout" else r["delivery_time"].replace("min", "").strip() + " min walk"
        lines.append(
            f"  {r['name']:<24} {stars:>6} {time_:>12} {r['price_range']:>14}"
        )
    lines.append(f"  {_LINE}")
    return "\n".join(lines)


# ── Main function ──────────────────────────────────────────────────────────────

def find_food(
    cuisine: Optional[str],
    lat: float,
    lng: float,
    dietary: str = "all",
    mode: str = "food",
    specific_foods: list = None,
    radius_km: float = 3,
    home_cookable: bool = False,
    trend_msg: str = "",
) -> dict:
    """Mock Swiggy API call. Returns realistic food suggestions."""

    cuisine = cuisine or "indian"
    specific_foods = specific_foods or []

    # Top detected foods for display (deduplicated, max 4)
    display_foods = list(dict.fromkeys(
        f for f in specific_foods if len(f) > 2
    ))[:4]
    foods_str = ", ".join(display_foods) if display_foods else cuisine

    trend_line = f"  🔥 {trend_msg}\n" if trend_msg else ""

    # ── Instamart ──────────────────────────────────────────────────────────────
    if mode == "instamart":
        category = _pick_instamart_category(cuisine, specific_foods, True, dietary)
        all_items = list(INSTAMART_ITEMS[category])
        random.shuffle(all_items)
        selected = all_items[:3]

        alert = (
            f"\n{'=' * 57}\n"
            f"  🛒  SWIGGY INSTAMART  —  10-15 min delivery\n"
            f"{'=' * 57}\n"
            f"{trend_line}"
            f"  Detected cravings : {foods_str}\n"
            f"  Category picked   : {category.title()}\n"
            f"\n  Your quick basket:\n"
            + _mini_table(selected, category)
            + f"\n  📍 Delivering to ({lat:.2f}, {lng:.2f})"
        )
        return {
            "mode":          "instamart",
            "category":      category,
            "items":         [{"name": n, "price_inr": p} for n, p in selected],
            "alert":         alert,
            "delivery_time": "10-15 min",
        }

    # ── Food Delivery ──────────────────────────────────────────────────────────
    restaurants = list(RESTAURANT_DATA.get(cuisine, RESTAURANT_DATA["indian"]))
    if dietary in ("gym", "diet") and "healthy" in RESTAURANT_DATA:
        restaurants = list(RESTAURANT_DATA["healthy"]) + restaurants
    random.shuffle(restaurants)
    top = restaurants[:2]

    if mode == "food":
        dietary_note = (
            f"\n  💪 Healthy options prioritised for your '{dietary}' profile!"
            if dietary in ("gym", "diet") else ""
        )
        alert = (
            f"\n{'=' * 57}\n"
            f"  🛵  SWIGGY FOOD DELIVERY\n"
            f"{'=' * 57}\n"
            f"{trend_line}"
            f"  Craving : {foods_str}\n"
            f"  Cuisine : {cuisine.title()}\n"
            f"\n  Top restaurants near you:\n"
            + _restaurant_table(top, "food")
            + dietary_note
            + f"\n  📍 Delivering to ({lat:.2f}, {lng:.2f})"
        )
        return {
            "mode":        "food",
            "restaurants": top,
            "alert":       alert,
        }

    # ── Dineout ────────────────────────────────────────────────────────────────
    dine_restaurants = list(RESTAURANT_DATA.get(cuisine, RESTAURANT_DATA["indian"]))
    random.shuffle(dine_restaurants)
    top_dine = dine_restaurants[:2]

    alert = (
        f"\n{'=' * 57}\n"
        f"  🍽️   DINEOUT  —  Top {cuisine.title()} restaurants near you\n"
        f"{'=' * 57}\n"
        f"{trend_line}"
        f"  Craving : {foods_str}\n"
        f"  Within  : {radius_km} km of your location\n"
        f"\n  Best picks:\n"
        + _restaurant_table(top_dine, "dineout")
        + f"\n  💡 Tip: Call ahead or book on Dineout app for a table.\n"
        + f"  📍 Near ({lat:.2f}, {lng:.2f})"
    )
    return {
        "mode":        "dineout",
        "restaurants": top_dine,
        "alert":       alert,
    }
