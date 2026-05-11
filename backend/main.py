"""
Cravyo Agent — FastAPI Backend
Full MVP server with all agent capabilities exposed as REST endpoints.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any
import json
import os
import uvicorn
from datetime import datetime
from pathlib import Path

# ── Env ────────────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

# ── Agent imports ──────────────────────────────────────────────────────────────
from feed_analyzer_agent import (
    run_agent,
    record_order as _record_order,
    record_skip as _record_skip,
    analyze_food,
    decide_swiggy_mode,
    call_swiggy,
    FeedState,
)
from nodes.price_comparison_node import price_comparison_node
from nodes.personalization_memory import UserMemory, DEFAULT_MEMORY_FILE

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Cravyo Agent API",
    description="Feed craving detection + smart food ordering agent",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response Models ──────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    username: str
    platform: str = "instagram"          # "instagram" | "youtube"
    dietary: str = "all"                  # all | veg | non-veg | gym | diet | vegan
    near_restaurant: bool = False
    location: dict = {"lat": 18.52, "lng": 73.85}

class MockAnalyzeRequest(BaseModel):
    """Run analysis against mock posts (no real scraping needed)."""
    posts: List[dict]
    dietary: str = "all"
    near_restaurant: bool = False
    time_context: str = "afternoon"       # morning | afternoon | evening | late_night
    location: dict = {"lat": 18.52, "lng": 73.85}
    city: str = "Pune"

class OrderRequest(BaseModel):
    restaurant: str
    dish: str
    channel: str = "food_delivery"        # food_delivery | instamart | dineout
    price: Optional[float] = None
    cuisine: Optional[str] = None
    rating: Optional[int] = None          # 1-5

class SkipRequest(BaseModel):
    restaurant: str

class PriceCompareRequest(BaseModel):
    dish: str
    city: str = "Pune"

class RateRequest(BaseModel):
    rating: int   # 1-5


# ── Helper ─────────────────────────────────────────────────────────────────────

def _build_mock_state(req: MockAnalyzeRequest) -> FeedState:
    from nodes.personalization_memory import load_user_memory_node
    base: FeedState = FeedState(
        username="mockuser", platform="instagram",
        posts=req.posts, food_detected=False,
        cuisine=None, specific_foods=[], is_snack=False,
        confidence=0.0, home_cookable=False,
        near_restaurant=req.near_restaurant, dietary=req.dietary,
        location=req.location,
        swiggy_mode=None, swiggy_result=None,
        alert_message=None, time_context=req.time_context,
        user_memory=None, user_preference_prompt="",
        skipped_restaurants=[], top_dishes=[], top_restaurants=[],
        ordered_dish=None, ordered_restaurant=None,
        order_channel=None, order_price_inr=None,
        order_cuisine=None, order_rating=None,
        skipped_restaurant=None, memory_saved=False,
        dish=None, city=req.city,
        price_comparison=None, price_comparison_text=None,
    )
    return load_user_memory_node(base)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "Cravyo Agent API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "groq_configured": bool(os.getenv("GROQ_API_KEY")),
        "apify_configured": bool(os.getenv("APIFY_API_TOKEN")),
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/analyze")
def analyze_real_feed(req: AnalyzeRequest):
    """
    Full pipeline: scrape → analyze → price compare → Swiggy suggestion.
    Uses real Instagram / YouTube scraping via Apify.
    """
    try:
        alert = run_agent(
            username=req.username,
            platform=req.platform,
            dietary=req.dietary,
            near_restaurant=req.near_restaurant,
            location=req.location,
        )
        return {"success": True, "result": alert, "username": req.username}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/mock")
def analyze_mock_feed(req: MockAnalyzeRequest):
    """
    Run the analysis pipeline against custom posts (no scraping needed).
    Great for demos, testing, and the frontend demo flow.
    """
    try:
        state = _build_mock_state(req)
        s1 = analyze_food(state)

        if not s1["food_detected"] or not s1["cuisine"]:
            return {
                "success": True,
                "food_detected": False,
                "message": "No food cravings detected in these posts.",
                "analysis": None,
                "swiggy": None,
                "price_comparison": None,
            }

        s2 = decide_swiggy_mode(s1)
        s3 = price_comparison_node(s2)
        s4 = call_swiggy(s3)

        return {
            "success": True,
            "food_detected": True,
            "analysis": {
                "cuisine": s4["cuisine"],
                "specific_foods": s4["specific_foods"],
                "is_snack": s4["is_snack"],
                "confidence": round(s4["confidence"], 2),
                "home_cookable": s4["home_cookable"],
                "time_context": s4["time_context"],
                "swiggy_mode": s4["swiggy_mode"],
            },
            "swiggy": s4.get("swiggy_result"),
            "price_comparison": s4.get("price_comparison"),
            "price_comparison_text": s4.get("price_comparison_text"),
            "alert": s4.get("alert_message"),
            "top_dishes": s4.get("top_dishes", []),
            "top_restaurants": s4.get("top_restaurants", []),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/price-compare")
def price_compare(req: PriceCompareRequest):
    """Compare prices for a dish across Instamart, Food Delivery, and Dineout."""
    try:
        dummy_state = {
            "dish": req.dish,
            "city": req.city,
            "messages": [],
        }
        result = price_comparison_node(dummy_state)
        return {
            "success": True,
            "dish": req.dish,
            "city": req.city,
            "comparison": result.get("price_comparison"),
            "summary": result.get("price_comparison_text"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/order")
def record_order(req: OrderRequest):
    """Record a confirmed order into user memory."""
    try:
        _record_order(
            restaurant=req.restaurant,
            dish=req.dish,
            channel=req.channel,
            price=req.price,
            cuisine=req.cuisine,
            rating=req.rating,
        )
        return {"success": True, "message": f"Order recorded: {req.dish} from {req.restaurant}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/skip")
def skip_restaurant(req: SkipRequest):
    """Record that the user dismissed a restaurant suggestion."""
    try:
        _record_skip(req.restaurant)
        return {"success": True, "message": f"Skipped: {req.restaurant}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rate-last-order")
def rate_last_order(req: RateRequest):
    """Rate the most recent order (1-5 stars)."""
    try:
        mem = UserMemory()
        mem.rate_last_order(req.rating)
        mem.save()
        return {"success": True, "rating_applied": req.rating}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory")
def get_memory():
    """Retrieve current user preferences / memory summary."""
    try:
        mem = UserMemory()
        return {
            "success": True,
            "summary": mem.summary_for_prompt(),
            "top_restaurants": mem.top_restaurants(10),
            "top_dishes": mem.top_dishes(10),
            "top_cuisines": mem.top_cuisines(5),
            "skipped_restaurants": mem.get_skipped_restaurants(),
            "order_history": mem.data.get("order_history", [])[-20:],  # last 20
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memory")
def clear_memory():
    """Clear all user preferences (reset)."""
    try:
        if DEFAULT_MEMORY_FILE.exists():
            DEFAULT_MEMORY_FILE.unlink()
        return {"success": True, "message": "Memory cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trends")
def get_trends():
    """Return craving trend data for the past 30 days."""
    trend_file = Path(__file__).parent / "craving_trends.json"
    if not trend_file.exists():
        return {"success": True, "trends": {}}
    with open(trend_file) as f:
        data = json.load(f)
    # Count per cuisine for last 30 days
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    summary = {c: sum(1 for d in dates if d >= cutoff) for c, dates in data.items()}
    summary = dict(sorted(summary.items(), key=lambda x: x[1], reverse=True))
    return {"success": True, "trends": summary, "raw": data}


# ── Demo posts helper ──────────────────────────────────────────────────────────

DEMO_POST_SETS = {
    "chinese": [
        {"caption": "Amazing dim sum and wonton soup tonight! #chinesefood", "hashtags": ["chinesefood", "dimsum"], "thumbnail_url": ""},
        {"caption": "Obsessed with kung pao chicken #chinesecuisine", "hashtags": ["chinesecuisine"], "thumbnail_url": ""},
        {"caption": "Best hakka noodles in the city! #hakka", "hashtags": ["hakka", "noodles"], "thumbnail_url": ""},
    ],
    "snacks": [
        {"caption": "Can't stop eating these chips! #snacks #junkfood", "hashtags": ["chips", "snacks"], "thumbnail_url": ""},
        {"caption": "Ice cream is life!! #icecream #dessert", "hashtags": ["icecream", "dessert"], "thumbnail_url": ""},
        {"caption": "Chocolate brownie obsession #chocolate #brownie", "hashtags": ["chocolate", "brownie"], "thumbnail_url": ""},
    ],
    "indian": [
        {"caption": "Sunday biryani is non-negotiable 🍛 #biryani #indianfood", "hashtags": ["biryani", "indianfood"], "thumbnail_url": ""},
        {"caption": "Maa ke hath ka dal chawal 😍 #dalrice #homefood", "hashtags": ["dal", "homefood"], "thumbnail_url": ""},
        {"caption": "Vada pav is the GOAT street food #vadapav #mumbai", "hashtags": ["vadapav", "streetfood"], "thumbnail_url": ""},
    ],
    "gym": [
        {"caption": "Post leg day recovery meal #gym #fitness #protein", "hashtags": ["gym", "fitness", "protein"], "thumbnail_url": ""},
        {"caption": "High protein low carb diet is working! #gymlife", "hashtags": ["gym", "workout", "diet"], "thumbnail_url": ""},
        {"caption": "Grilled chicken + quinoa = gains 💪 #cleaneating", "hashtags": ["healthy", "protein"], "thumbnail_url": ""},
    ],
    "italian": [
        {"caption": "Carbonara night 🍝 #pasta #italian #carbonara", "hashtags": ["pasta", "italian"], "thumbnail_url": ""},
        {"caption": "Homemade pizza is a religion #pizza #pizzanight", "hashtags": ["pizza", "homemade"], "thumbnail_url": ""},
        {"caption": "Tiramisu from scratch — worth every minute #tiramisu #dessert", "hashtags": ["tiramisu", "italian"], "thumbnail_url": ""},
    ],
}

@app.get("/demo-posts/{preset}")
def get_demo_posts(preset: str):
    """Return pre-made demo posts for frontend demos."""
    posts = DEMO_POST_SETS.get(preset)
    if not posts:
        raise HTTPException(status_code=404, detail=f"Unknown preset: {preset}. Options: {list(DEMO_POST_SETS.keys())}")
    return {"preset": preset, "posts": posts}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
