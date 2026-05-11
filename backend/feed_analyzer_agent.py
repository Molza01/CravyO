from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv
from instagram_service import scrape_instagram
from youtube_service import scrape_youtube
from swiggy_service import find_food

# ── New feature imports ────────────────────────────────────────────────────────
from nodes.personalization_memory import load_user_memory_node, save_user_memory_node, UserMemory
from nodes.price_comparison_node import price_comparison_node

import json, os, re

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)

# ── Constants ──────────────────────────────────────────────────────────────────
TREND_FILE = "craving_trends.json"

INSTAMART_TRIGGERS = [
    "chips", "biscuit", "cookie", "chocolate", "ice cream", "icecream",
    "maggi", "popcorn", "candy", "wafer", "snack", "juice", "coffee",
    "tea", "smoothie", "milkshake", "soda", "cola", "energy drink",
    "protein bar", "muesli", "cereal", "yogurt", "curd", "brownie",
]

FOOD_CUISINE_MAP = {
    "biryani": "indian",    "curry": "indian",    "dal": "indian",
    "roti": "indian",       "naan": "indian",      "paneer": "indian",
    "butter chicken": "indian", "samosa": "indian", "dosa": "indian",
    "idli": "indian",       "tikka": "indian",     "chole": "indian",
    "rajma": "indian",      "masala": "indian",    "thali": "indian",
    "kebab": "indian",      "korma": "indian",     "chapati": "indian",
    "pav bhaji": "indian",  "vada pav": "indian",  "poha": "indian",

    "pizza": "italian",     "pasta": "italian",    "risotto": "italian",
    "lasagna": "italian",   "tiramisu": "italian", "gelato": "italian",
    "carbonara": "italian", "calzone": "italian",  "bruschetta": "italian",

    "dumpling": "chinese",  "dim sum": "chinese",  "kung pao": "chinese",
    "fried rice": "chinese","manchurian": "chinese","hakka": "chinese",
    "wonton": "chinese",    "chowmein": "chinese", "spring roll": "chinese",
    "szechuan": "chinese",  "peking": "chinese",

    "pad thai": "thai",     "green curry": "thai", "tom yum": "thai",
    "satay": "thai",        "massaman": "thai",

    "taco": "mexican",      "burrito": "mexican",  "quesadilla": "mexican",
    "guacamole": "mexican", "enchilada": "mexican","nachos": "mexican",

    "cake": "desserts",     "brownie": "desserts", "pastry": "desserts",
    "ice cream": "desserts","dessert": "desserts", "cheesecake": "desserts",
    "waffle": "desserts",   "macaron": "desserts", "cookie": "desserts",
    "chocolate": "desserts",

    "burger": "american",   "hot dog": "american", "steak": "american",
    "bbq": "american",      "fries": "american",
}

DIETARY_AVOID = {
    "gym":    ["fried", "chips", "chocolate", "cake", "ice cream", "candy"],
    "diet":   ["fried", "heavy", "rich", "creamy", "cheese"],
    "veg":    ["chicken", "mutton", "fish", "prawn", "egg", "meat", "beef"],
    "vegan":  ["chicken", "mutton", "fish", "dairy", "egg", "cheese",
               "butter", "cream", "milk", "ghee"],
    "non-veg": [],
    "all":    [],
}


# ── State ──────────────────────────────────────────────────────────────────────
class FeedState(TypedDict):
    username: str
    platform: str
    posts: list
    food_detected: bool
    cuisine: Optional[str]
    specific_foods: list
    is_snack: bool
    confidence: float
    home_cookable: bool
    near_restaurant: bool
    dietary: str
    location: dict
    swiggy_mode: Optional[str]
    swiggy_result: Optional[dict]
    alert_message: Optional[str]
    time_context: str

    # ── Personalisation memory ─────────────────────────────────────────────────
    user_memory: Any                   # UserMemory object (in-memory, not saved to JSON)
    user_preference_prompt: str        # injected into LLM prompts
    skipped_restaurants: list          # restaurants to filter out of suggestions
    top_dishes: list                   # user's most-ordered dishes
    top_restaurants: list              # user's favourite restaurants
    ordered_dish: Optional[str]        # set after user confirms order
    ordered_restaurant: Optional[str]
    order_channel: Optional[str]
    order_price_inr: Optional[float]
    order_cuisine: Optional[str]
    order_rating: Optional[int]
    skipped_restaurant: Optional[Any]  # str or list[str]
    memory_saved: bool

    # ── Price comparison ───────────────────────────────────────────────────────
    dish: Optional[str]                # top detected food — used by price_comparison_node
    city: Optional[str]                # derived from location
    price_comparison: Optional[dict]
    price_comparison_text: Optional[str]


# ── Trend Tracker ──────────────────────────────────────────────────────────────
def load_trends() -> dict:
    if os.path.exists(TREND_FILE):
        with open(TREND_FILE) as f:
            return json.load(f)
    return {}

def save_trend(cuisine: str):
    trends = load_trends()
    today = datetime.now().strftime("%Y-%m-%d")
    trends.setdefault(cuisine, []).append(today)
    with open(TREND_FILE, "w") as f:
        json.dump(trends, f)

def get_weekly_trend() -> Optional[str]:
    trends = load_trends()
    cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    counts = {c: sum(1 for d in dates if d >= cutoff)
              for c, dates in trends.items()}
    if not counts:
        return None
    top = max(counts, key=counts.get)
    return top if counts[top] >= 3 else None

def get_time_context(hour: int) -> str:
    if 5 <= hour < 11:    return "morning"
    elif 11 <= hour < 17: return "afternoon"
    elif 17 <= hour < 22: return "evening"
    else:                 return "late_night"


# ── JSON Cleaner ───────────────────────────────────────────────────────────────
def clean_and_parse_json(raw: str) -> dict:
    cleaned = raw.strip()
    if "```" in cleaned:
        match = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    cleaned = (cleaned.replace("True", "true")
                      .replace("False", "false")
                      .replace('"null"', "null"))
    try:
        return json.loads(cleaned)
    except Exception:
        return {}


# ── Keyword Detection ──────────────────────────────────────────────────────────
def detect_specific_foods(text: str) -> list:
    text_lower = text.lower()
    found = []
    for food in sorted(FOOD_CUISINE_MAP.keys(), key=len, reverse=True):
        if food in text_lower and food not in found:
            found.append(food)
    return found[:5]

def detect_snacks(text: str) -> list:
    text_lower = text.lower()
    return [s for s in INSTAMART_TRIGGERS if s in text_lower]

def infer_cuisine(foods: list) -> Optional[str]:
    if not foods:
        return None
    counts = {}
    for food in foods:
        c = FOOD_CUISINE_MAP.get(food)
        if c:
            counts[c] = counts.get(c, 0) + 1
    return max(counts, key=counts.get) if counts else None

def filter_by_diet(foods: list, dietary: str) -> list:
    avoid = DIETARY_AVOID.get(dietary, [])
    if not avoid:
        return foods
    return [f for f in foods if not any(a in f.lower() for a in avoid)]

def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "ignore").decode())

def analyze_thumbnail_vision(thumbnail_url: str) -> str:
    return "none"


# ── Graph Nodes ────────────────────────────────────────────────────────────────

def scrape_feed(state: FeedState) -> FeedState:
    print(f"\n[INFO] Scraping {state['platform']} for @{state['username']}...")
    if state["platform"] == "instagram":
        posts = scrape_instagram(state["username"], max_posts=15)
    else:
        posts = scrape_youtube(state["username"], max_videos=10)
    print(f"[INFO] Got {len(posts)} posts")
    if posts:
        sample = posts[0].get("caption", posts[0].get("title", ""))[:100]
        safe_print(f"[DEBUG] First post: {sample}")
    return {**state, "posts": posts}


def analyze_food(state: FeedState) -> FeedState:
    hour = datetime.now().hour
    time_context = get_time_context(hour)
    print(f"[INFO] Time: {time_context} | Dietary: {state['dietary']}")

    if not state["posts"]:
        print("[WARN] No posts to analyze")
        return {**state, "food_detected": False, "cuisine": None,
                "specific_foods": [], "is_snack": False,
                "confidence": 0.0, "home_cookable": False,
                "time_context": time_context, "dish": None}

    all_text = " ".join([
        p.get("caption", "") + " " + p.get("title", "") + " " +
        " ".join(p.get("hashtags", [])) + " " + " ".join(p.get("tags", []))
        for p in state["posts"]
    ])

    captions = "\n".join([
        f"- {p.get('caption', p.get('title', ''))[:200]}"
        for p in state["posts"][:10]
    ])

    specific_foods = detect_specific_foods(all_text)
    snacks = detect_snacks(all_text)
    keyword_cuisine = infer_cuisine(specific_foods)

    safe_print(f"[DEBUG] Keyword foods: {specific_foods}")
    safe_print(f"[DEBUG] Snacks: {snacks}")

    dietary_note = (f"\nUser dietary profile: {state['dietary']}. "
                    f"Note if food matches healthy eating."
                    if state["dietary"] in ["gym", "diet"] else "")

    # ── Inject user preferences into the LLM prompt ───────────────────────────
    preference_context = state.get("user_preference_prompt", "")
    preference_note = (f"\n\nUser food preferences (personalised):\n{preference_context}"
                       if preference_context else "")

    prompt = f"""Analyze these social media posts to detect food items and cravings.
Time of day: {time_context}{dietary_note}{preference_note}

Posts:
{captions}

Return ONLY raw JSON (no markdown, no explanation):
{{
  "food_detected": true or false,
  "cuisine": "indian or chinese or italian or thai or mexican or desserts or american or null",
  "specific_foods": ["exact food items mentioned like biryani, chips, ice cream"],
  "is_snack": true if snacks or packaged food detected,
  "confidence": 0.0 to 1.0,
  "home_cookable": true or false
}}"""

    parsed = {}
    try:
        result = llm.invoke(prompt)
        raw = result.content if hasattr(result, "content") else str(result)
        safe_print(f"[DEBUG] LLM: {raw[:300]}")
        parsed = clean_and_parse_json(raw)
        safe_print(f"[DEBUG] Parsed: {parsed}")
    except Exception as e:
        print(f"[ERROR] LLM failed: {e}")

    cuisine = parsed.get("cuisine")
    if cuisine in [None, "null", "None", ""]:
        cuisine = keyword_cuisine

    llm_foods = parsed.get("specific_foods", [])
    if isinstance(llm_foods, list):
        all_foods = list(set(specific_foods + llm_foods + snacks))
    else:
        all_foods = list(set(specific_foods + snacks))

    all_foods = filter_by_diet(all_foods, state["dietary"])

    food_detected = parsed.get("food_detected", bool(all_foods or cuisine))
    confidence    = float(parsed.get("confidence", 0.75 if all_foods else 0.0))
    is_snack      = parsed.get("is_snack", False) or bool(snacks)
    home_cookable = parsed.get("home_cookable", False)

    if is_snack and not cuisine:
        cuisine = "desserts"

    # Pick the top dish for price comparison
    top_dish = all_foods[0] if all_foods else cuisine

    if food_detected and cuisine:
        save_trend(cuisine)
        foods_str = ", ".join(all_foods[:3]) if all_foods else cuisine
        safe_print(f"[INFO] Detected: {foods_str} | cuisine={cuisine} | "
                   f"snack={is_snack} | confidence={confidence:.0%}")
    else:
        print("[INFO] No food detected in posts")

    return {**state,
            "food_detected": food_detected,
            "cuisine": cuisine,
            "specific_foods": all_foods,
            "is_snack": is_snack,
            "confidence": confidence,
            "home_cookable": home_cookable,
            "time_context": time_context,
            "dish": top_dish}          # ← feeds into price_comparison_node


def decide_swiggy_mode(state: FeedState) -> FeedState:
    hour = datetime.now().hour
    time_context = state["time_context"]
    dietary = state["dietary"]

    if time_context == "late_night" or (time_context == "morning" and hour < 7):
        mode, reason = "instamart", "late night / early morning"
    elif state["is_snack"]:
        mode, reason = "instamart", "snack/packaged food detected in feed"
    elif state["near_restaurant"] and time_context in ["afternoon", "evening"]:
        mode, reason = "dineout", "near restaurant during dining hours"
    elif dietary in ["gym", "diet"]:
        mode, reason = "food", f"dietary profile: {dietary} (healthy delivery)"
    elif state["home_cookable"] and time_context == "evening":
        mode, reason = "instamart", "home-cookable dish — get ingredients"
    else:
        mode, reason = "food", "standard food delivery"

    trend = get_weekly_trend()
    trend_msg = ""
    if trend and trend == state["cuisine"]:
        trend_msg = f"You've been craving {trend} all week!"

    print(f"[INFO] Swiggy mode: {mode} | {reason}")
    return {**state, "swiggy_mode": mode,
            "alert_message": trend_msg or None}


def call_swiggy(state: FeedState) -> FeedState:
    # Filter out restaurants the user has repeatedly skipped
    skipped = state.get("skipped_restaurants", [])
    if skipped:
        print(f"[INFO] Skipping restaurants (user preference): {skipped}")

    trend_msg = state.get("alert_message") or ""

    result = find_food(
        cuisine=state["cuisine"],
        lat=state["location"].get("lat", 18.52),
        lng=state["location"].get("lng", 73.85),
        dietary=state["dietary"],
        mode=state["swiggy_mode"],
        specific_foods=state["specific_foods"],
        radius_km=3,
        home_cookable=state.get("home_cookable", False),
        trend_msg=trend_msg,
    )

    # Append price comparison text to the final alert if available
    price_text = state.get("price_comparison_text", "")
    final_alert = result.get("alert", "No suggestions found.")
    if price_text:
        final_alert = final_alert + "\n\n" + price_text

    return {**state, "swiggy_result": result, "alert_message": final_alert}


# ── Routing ────────────────────────────────────────────────────────────────────
def should_continue(state: FeedState) -> str:
    if not state["food_detected"] or not state["cuisine"]:
        print("[INFO] No food detected — pipeline stopped")
        return END
    return "decide_mode"


# ── Build Graph ────────────────────────────────────────────────────────────────
graph = StateGraph(FeedState)

# Existing nodes
graph.add_node("scrape", scrape_feed)
graph.add_node("analyze", analyze_food)
graph.add_node("decide_mode", decide_swiggy_mode)
graph.add_node("call_swiggy", call_swiggy)

# ★ New nodes
graph.add_node("load_memory", load_user_memory_node)
graph.add_node("compare_prices", price_comparison_node)
graph.add_node("save_memory", save_user_memory_node)

# ── Edges ──────────────────────────────────────────────────────────────────────
graph.set_entry_point("load_memory")           # ★ memory loads first
graph.add_edge("load_memory", "scrape")        # then scrape as before
graph.add_edge("scrape", "analyze")
graph.add_conditional_edges("analyze", should_continue)
graph.add_edge("decide_mode", "compare_prices")  # ★ price comparison added
graph.add_edge("compare_prices", "call_swiggy")
graph.add_edge("call_swiggy", "save_memory")        # ★ save memory last
graph.add_edge("save_memory", END)

compiled = graph.compile()


# ── Run Agent ──────────────────────────────────────────────────────────────────
def run_agent(username: str, platform: str = "instagram",
              dietary: str = "all", near_restaurant: bool = False,
              location: dict = None) -> str:
    if location is None:
        location = {"lat": 18.52, "lng": 73.85}

    # Derive city name from coordinates (simple lookup — extend as needed)
    city = "Pune"   # default; replace with reverse-geocode if you have one

    initial_state = FeedState(
        username=username, platform=platform, posts=[],
        food_detected=False, cuisine=None, specific_foods=[],
        is_snack=False, confidence=0.0, home_cookable=False,
        near_restaurant=near_restaurant, dietary=dietary,
        location=location, swiggy_mode=None, swiggy_result=None,
        alert_message=None, time_context="afternoon",
        # ★ memory fields (load_user_memory_node fills these in)
        user_memory=None, user_preference_prompt="",
        skipped_restaurants=[], top_dishes=[], top_restaurants=[],
        ordered_dish=None, ordered_restaurant=None,
        order_channel=None, order_price_inr=None,
        order_cuisine=None, order_rating=None,
        skipped_restaurant=None, memory_saved=False,
        # ★ price comparison fields
        dish=None, city=city,
        price_comparison=None, price_comparison_text=None,
    )
    result = compiled.invoke(initial_state)
    return result.get("alert_message") or \
           "No food cravings detected in your feed right now."


# ── Helper: record what the user actually ordered (call after confirmation) ────
def record_order(restaurant: str, dish: str, channel: str = "food_delivery",
                 price: float = None, cuisine: str = None, rating: int = None):
    """
    Call this after the user confirms an order so the memory is updated.
    Example:
        record_order("Behrouz Biryani", "Chicken Biryani", price=349, cuisine="indian")
    """
    mem = UserMemory()
    mem.record_order(dish=dish, restaurant=restaurant, channel=channel,
                     price_inr=price, cuisine=cuisine, rating=rating)
    mem.save()
    print(f"[MEMORY] Saved order: {dish} from {restaurant}")


def record_skip(restaurant: str):
    """
    Call this when the user dismisses a restaurant suggestion.
    After 2 skips it will stop appearing.
    """
    mem = UserMemory()
    mem.record_skip(restaurant)
    mem.save()
    print(f"[MEMORY] Recorded skip: {restaurant}")


# ── Main Menu ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  FeedCraving Agent - LangGraph + Swiggy")
    print("=" * 55)

    while True:
        print("\nOptions:")
        print("  1. Analyze Instagram feed")
        print("  2. Analyze YouTube feed")
        print("  3. Quick test - Chinese food (Dineout)")
        print("  4. Quick test - Chips & Ice cream (Instamart)")
        print("  5. Quick test - Gym user (Healthy options)")
        print("  6. Record an order (update memory)")
        print("  7. Skip a restaurant (update memory)")
        print("  8. Exit")

        choice = input("\nChoice: ").strip()

        if choice == "1":
            username = input("Instagram username: ").strip()
            print("Dietary options: all | veg | non-veg | gym | diet | vegan")
            dietary = input("Your dietary profile: ").strip() or "all"
            near = input("Near a restaurant? (y/n): ").strip().lower() == "y"
            alert = run_agent(username, "instagram", dietary, near)
            print(f"\n{'='*55}\n{alert}\n{'='*55}")

        elif choice == "2":
            channel = input("YouTube channel handle: ").strip()
            print("Dietary options: all | veg | non-veg | gym | diet | vegan")
            dietary = input("Your dietary profile: ").strip() or "all"
            near = input("Near a restaurant? (y/n): ").strip().lower() == "y"
            alert = run_agent(channel, "youtube", dietary, near)
            print(f"\n{'='*55}\n{alert}\n{'='*55}")

        elif choice == "3":
            print("\n[TEST] Chinese food - user near a restaurant (Dineout)...")
            mock_posts = [
                {"caption": "Amazing dim sum and wonton soup tonight! #chinesefood",
                 "hashtags": ["chinesefood", "dimsum"], "thumbnail_url": ""},
                {"caption": "Obsessed with kung pao chicken #chinesecuisine",
                 "hashtags": ["chinesecuisine"], "thumbnail_url": ""},
                {"caption": "Best hakka noodles in the city! Must try",
                 "hashtags": ["hakka", "noodles"], "thumbnail_url": ""},
            ]
            test_state = FeedState(
                username="testuser", platform="instagram",
                posts=mock_posts, food_detected=False,
                cuisine=None, specific_foods=[], is_snack=False,
                confidence=0.0, home_cookable=False,
                near_restaurant=True, dietary="all",
                location={"lat": 18.52, "lng": 73.85},
                swiggy_mode=None, swiggy_result=None,
                alert_message=None, time_context="afternoon",
                user_memory=None, user_preference_prompt="",
                skipped_restaurants=[], top_dishes=[], top_restaurants=[],
                ordered_dish=None, ordered_restaurant=None,
                order_channel=None, order_price_inr=None,
                order_cuisine=None, order_rating=None,
                skipped_restaurant=None, memory_saved=False,
                dish=None, city="Pune",
                price_comparison=None, price_comparison_text=None,
            )
            s1 = analyze_food(test_state)
            s2 = decide_swiggy_mode(s1)
            s3 = price_comparison_node(s2)
            s4 = call_swiggy(s3)
            print(f"\n{'='*55}\n{s4['alert_message']}\n{'='*55}")

        elif choice == "4":
            print("\n[TEST] Snack feed - Instamart suggestion...")
            mock_posts = [
                {"caption": "Can't stop eating these chips! #snacks #junkfood",
                 "hashtags": ["chips", "snacks"], "thumbnail_url": ""},
                {"caption": "Ice cream is life!! #icecream #dessert",
                 "hashtags": ["icecream", "dessert"], "thumbnail_url": ""},
                {"caption": "Chocolate brownie obsession #chocolate #brownie",
                 "hashtags": ["chocolate", "brownie"], "thumbnail_url": ""},
            ]
            test_state = FeedState(
                username="testuser", platform="instagram",
                posts=mock_posts, food_detected=False,
                cuisine=None, specific_foods=[], is_snack=False,
                confidence=0.0, home_cookable=False,
                near_restaurant=False, dietary="all",
                location={"lat": 18.52, "lng": 73.85},
                swiggy_mode=None, swiggy_result=None,
                alert_message=None, time_context="evening",
                user_memory=None, user_preference_prompt="",
                skipped_restaurants=[], top_dishes=[], top_restaurants=[],
                ordered_dish=None, ordered_restaurant=None,
                order_channel=None, order_price_inr=None,
                order_cuisine=None, order_rating=None,
                skipped_restaurant=None, memory_saved=False,
                dish=None, city="Pune",
                price_comparison=None, price_comparison_text=None,
            )
            s1 = analyze_food(test_state)
            s2 = decide_swiggy_mode(s1)
            s3 = price_comparison_node(s2)
            s4 = call_swiggy(s3)
            print(f"\n{'='*55}\n{s4['alert_message']}\n{'='*55}")

        elif choice == "5":
            print("\n[TEST] Gym user feed - Healthy suggestions...")
            mock_posts = [
                {"caption": "Post leg day recovery meal #gym #fitness #protein",
                 "hashtags": ["gym", "fitness", "protein"], "thumbnail_url": ""},
                {"caption": "High protein low carb diet is working! #gymlife",
                 "hashtags": ["gym", "workout", "diet"], "thumbnail_url": ""},
                {"caption": "Biryani after workout? No way! Salad it is.",
                 "hashtags": ["healthy", "salad"], "thumbnail_url": ""},
            ]
            test_state = FeedState(
                username="testuser", platform="instagram",
                posts=mock_posts, food_detected=False,
                cuisine=None, specific_foods=[], is_snack=False,
                confidence=0.0, home_cookable=False,
                near_restaurant=False, dietary="gym",
                location={"lat": 18.52, "lng": 73.85},
                swiggy_mode=None, swiggy_result=None,
                alert_message=None, time_context="morning",
                user_memory=None, user_preference_prompt="",
                skipped_restaurants=[], top_dishes=[], top_restaurants=[],
                ordered_dish=None, ordered_restaurant=None,
                order_channel=None, order_price_inr=None,
                order_cuisine=None, order_rating=None,
                skipped_restaurant=None, memory_saved=False,
                dish=None, city="Pune",
                price_comparison=None, price_comparison_text=None,
            )
            s1 = analyze_food(test_state)
            s2 = decide_swiggy_mode(s1)
            s3 = price_comparison_node(s2)
            s4 = call_swiggy(s3)
            print(f"\n{'='*55}\n{s4['alert_message']}\n{'='*55}")

        elif choice == "6":
            restaurant = input("Restaurant name: ").strip()
            dish = input("Dish ordered: ").strip()
            price = input("Price paid (₹): ").strip()
            cuisine = input("Cuisine type (optional): ").strip() or None
            rating = input("Rating 1-5 (optional): ").strip()
            record_order(
                restaurant=restaurant, dish=dish,
                price=float(price) if price else None,
                cuisine=cuisine,
                rating=int(rating) if rating else None,
            )

        elif choice == "7":
            restaurant = input("Restaurant to skip: ").strip()
            record_skip(restaurant)

        elif choice == "8":
            print("Goodbye!")
            break

        else:
            print("Invalid choice, try again.")