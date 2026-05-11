"""
Request + response schemas for cravyo-agent.

These models are auto-advertised at /.well-known/agent-card.json as
`input_schema` and `output_schema` so callers can discover the full
contract without reading source code.

──────────────────────────────────────────────────────────────────────
REQUEST FORMAT
──────────────────────────────────────────────────────────────────────
Send a JSON body with an "action" field to call a specific capability:

  analyze              — scrape a real feed and detect food cravings
  analyze_mock         — run the pipeline on caller-supplied posts
  compare_prices       — compare a dish price across channels
  record_order         — persist a confirmed order to user memory
  skip                 — dismiss a restaurant (stops appearing after 2x)
  rate_last_order      — rate the most recent order 1-5 stars
  get_memory           — retrieve user preferences and order history
  clear_memory         — wipe all stored preferences
  get_trends           — craving trends over the past 30 days
  get_demo_posts       — return a preset demo post batch for testing

Plain-text (no "action") is routed to the LangChain conversational agent.

Examples:

  {"action": "analyze", "username": "foodie_reel",
   "platform": "instagram", "dietary": "veg",
   "near_restaurant": true}

  {"action": "analyze_mock",
   "posts": [{"caption": "biryani tonight!", "hashtags": ["biryani"], "thumbnail_url": ""}],
   "dietary": "all", "near_restaurant": false,
   "time_context": "evening", "city": "Pune"}

  {"action": "compare_prices", "dish": "chicken biryani", "city": "Mumbai"}

  {"action": "record_order", "restaurant": "Behrouz Biryani",
   "dish": "Chicken Biryani", "channel": "food_delivery",
   "price": 349, "cuisine": "indian", "rating": 5}

  {"action": "skip", "restaurant": "McDonald's"}

  {"action": "rate_last_order", "rating": 4}

  {"action": "get_memory"}

  {"action": "clear_memory"}

  {"action": "get_trends"}

  {"action": "get_demo_posts", "preset": "chinese"}
"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from zyndai_agent import AgentPayload, Attachment


class RequestPayload(AgentPayload):
    """
    Cravyo-agent inbound message schema.

    Set `action` to one of the supported values to invoke a specific
    capability.  Omit it (or send plain text) for conversational mode.
    """

    action: Optional[
        Literal[
            "analyze",
            "analyze_mock",
            "compare_prices",
            "record_order",
            "skip",
            "rate_last_order",
            "get_memory",
            "clear_memory",
            "get_trends",
            "get_demo_posts",
        ]
    ] = Field(
        default=None,
        description="Which cravyo capability to invoke. Omit for chat mode.",
    )

    # ── analyze ─────────────────────────────────────────────────────────────
    username: Optional[str] = Field(
        default=None,
        description="Instagram username or YouTube channel handle.",
    )
    platform: Literal["instagram", "youtube"] = Field(
        default="instagram",
        description="Social platform to scrape.",
    )
    dietary: Literal["all", "veg", "non-veg", "gym", "diet", "vegan"] = Field(
        default="all",
        description="Dietary profile filter for suggestions.",
    )
    near_restaurant: bool = Field(
        default=False,
        description="Whether the user is currently near a restaurant (enables Dineout mode).",
    )
    location: dict = Field(
        default={"lat": 18.52, "lng": 73.85},
        description="User GPS coordinates {lat, lng} for city-aware suggestions.",
    )

    # ── analyze_mock ─────────────────────────────────────────────────────────
    posts: Optional[list[dict]] = Field(
        default=None,
        description="Pre-supplied post list for analyze_mock. "
                    "Each item: {caption, hashtags, thumbnail_url}.",
    )
    time_context: Literal["morning", "afternoon", "evening", "late_night"] = Field(
        default="afternoon",
        description="Time of day — affects suggestion tone.",
    )
    city: str = Field(
        default="Pune",
        description="City name for price comparison (used in analyze_mock and compare_prices).",
    )

    # ── compare_prices ───────────────────────────────────────────────────────
    dish: Optional[str] = Field(
        default=None,
        description="Dish name to price-compare across channels.",
    )

    # ── record_order ─────────────────────────────────────────────────────────
    restaurant: Optional[str] = Field(
        default=None,
        description="Restaurant name for record_order and skip actions.",
    )
    channel: Literal["food_delivery", "instamart", "dineout"] = Field(
        default="food_delivery",
        description="Order channel for record_order.",
    )
    price: Optional[float] = Field(
        default=None,
        description="Order price in INR.",
    )
    cuisine: Optional[str] = Field(
        default=None,
        description="Cuisine type of the order (e.g. 'indian', 'chinese').",
    )

    # ── rate_last_order ──────────────────────────────────────────────────────
    rating: Optional[int] = Field(
        default=None,
        ge=1, le=5,
        description="Star rating 1-5 for the most recent order.",
    )

    # ── get_demo_posts ───────────────────────────────────────────────────────
    preset: Optional[
        Literal["chinese", "snacks", "indian", "gym", "italian"]
    ] = Field(
        default=None,
        description="Demo post preset name to fetch for testing.",
    )

    # ── multi-platform fusion ──────────────────────────────────────────────
    multi_platform_cravings: Optional[list[dict]] = Field(
        default=None,
        description="List of cravings from multiple platforms. "
                    "Each dict: {platform, food, confidence, detected_at, frequency}.",
    )


class ResponsePayload(BaseModel):
    """
    Cravyo-agent response envelope.

    `extra = 'allow'` means action-specific fields (e.g. 'analysis',
    'swiggy', 'price_comparison', 'trends') pass through without being
    stripped.
    """

    model_config = ConfigDict(extra="allow")

    # Common envelope
    response: str = Field(default="", description="Human-readable reply (chat mode).")
    success: Optional[bool] = Field(default=None, description="True on success, False on error.")
    error: Optional[str] = Field(default=None, description="Error message if success is False.")

    # analyze / analyze_mock
    result: Optional[str] = Field(default=None, description="Alert message from analyze action.")
    food_detected: Optional[bool] = Field(default=None)
    analysis: Optional[dict] = Field(default=None)
    swiggy: Optional[dict] = Field(default=None)
    price_comparison: Optional[Any] = Field(default=None)
    price_comparison_text: Optional[str] = Field(default=None)
    alert: Optional[str] = Field(default=None)
    top_dishes: Optional[list] = Field(default=None)
    top_restaurants: Optional[list] = Field(default=None)

    # compare_prices
    comparison: Optional[Any] = Field(default=None)
    summary: Optional[str] = Field(default=None)

    # get_memory
    top_cuisines: Optional[list] = Field(default=None)
    skipped_restaurants: Optional[list] = Field(default=None)
    order_history: Optional[list] = Field(default=None)

    # get_trends
    trends: Optional[dict] = Field(default=None)

    # get_demo_posts
    posts: Optional[list] = Field(default=None)
    preset: Optional[str] = Field(default=None)

    # multi-platform fusion
    fusion_result: Optional[dict] = Field(default=None)
    meal_nudge: Optional[dict] = Field(default=None)


# Cap on total A2A request body size. Tune per your needs.
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
