"""
cravyo-agent — Cravyo food-craving AI agent on the ZyndAI network.

Wraps the full cravyo backend (LangGraph feed-analyzer, price comparison,
personalization memory) as a ZyndAI agent so any other agent on the
network can call it via A2A.

Actions (send as JSON in the message body):

  {"action": "analyze", "username": "...", "platform": "instagram",
   "dietary": "all", "near_restaurant": false,
   "location": {"lat": 18.52, "lng": 73.85}}

  {"action": "analyze_mock", "posts": [...], "dietary": "all",
   "near_restaurant": false, "time_context": "afternoon",
   "location": {"lat": 18.52, "lng": 73.85}, "city": "Pune"}

  {"action": "compare_prices", "dish": "biryani", "city": "Pune"}

  {"action": "record_order", "restaurant": "Behrouz Biryani",
   "dish": "Chicken Biryani", "channel": "food_delivery",
   "price": 349, "cuisine": "indian", "rating": 5}

  {"action": "skip", "restaurant": "McDonald's"}

  {"action": "rate_last_order", "rating": 4}

  {"action": "get_memory"}

  {"action": "clear_memory"}

  {"action": "get_trends"}

  {"action": "get_demo_posts", "preset": "chinese"}

Any plain-text message (no "action" field) falls through to the
LangChain agent for natural-language conversation.

Install:
  pip install zyndai-agent langchain-groq langchain-classic \
              langchain-community langgraph
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# ── backend package (sibling directory) ───────────────────────────────────────
# Ensure this file's directory is on sys.path so `backend` resolves.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from backend import (
    FeedState,
    UserMemory,
    DEFAULT_MEMORY_FILE,
    analyze_food,
    call_swiggy,
    decide_swiggy_mode,
    price_comparison_node,
    record_order,
    record_skip,
    run_agent,
)

# ── ZyndAI SDK ─────────────────────────────────────────────────────────────────
from zyndai_agent import (
    A2AClient,
    AgentConfig,
    SearchAndDiscoveryManager,
    ZyndAIAgent,
    resolve_registry_url,
)
from zyndai_agent.a2a.server import HandlerInput, TaskHandle

# ── LangChain / Groq ───────────────────────────────────────────────────────────
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_groq import ChatGroq

# ── Local ──────────────────────────────────────────────────────────────────────
from payload import RequestPayload, ResponsePayload, MAX_FILE_SIZE_BYTES

# ── Agent config ───────────────────────────────────────────────────────────────
_config: dict = {}
if os.path.exists("agent.config.json"):
    with open("agent.config.json") as _f:
        _config = json.load(_f)


# ── Demo post sets (kept here so the agent can serve them without FastAPI) ─────
DEMO_POST_SETS: dict[str, list[dict]] = {
    "chinese": [
        {"caption": "Amazing dim sum and wonton soup tonight! #chinesefood",
         "hashtags": ["chinesefood", "dimsum"], "thumbnail_url": ""},
        {"caption": "Obsessed with kung pao chicken #chinesecuisine",
         "hashtags": ["chinesecuisine"], "thumbnail_url": ""},
        {"caption": "Best hakka noodles in the city! #hakka",
         "hashtags": ["hakka", "noodles"], "thumbnail_url": ""},
    ],
    "snacks": [
        {"caption": "Can't stop eating these chips! #snacks #junkfood",
         "hashtags": ["chips", "snacks"], "thumbnail_url": ""},
        {"caption": "Ice cream is life!! #icecream #dessert",
         "hashtags": ["icecream", "dessert"], "thumbnail_url": ""},
        {"caption": "Chocolate brownie obsession #chocolate #brownie",
         "hashtags": ["chocolate", "brownie"], "thumbnail_url": ""},
    ],
    "indian": [
        {"caption": "Sunday biryani is non-negotiable 🍛 #biryani #indianfood",
         "hashtags": ["biryani", "indianfood"], "thumbnail_url": ""},
        {"caption": "Maa ke hath ka dal chawal 😍 #dalrice #homefood",
         "hashtags": ["dal", "homefood"], "thumbnail_url": ""},
        {"caption": "Vada pav is the GOAT street food #vadapav #mumbai",
         "hashtags": ["vadapav", "streetfood"], "thumbnail_url": ""},
    ],
    "gym": [
        {"caption": "Post leg day recovery meal #gym #fitness #protein",
         "hashtags": ["gym", "fitness", "protein"], "thumbnail_url": ""},
        {"caption": "High protein low carb diet is working! #gymlife",
         "hashtags": ["gym", "workout", "diet"], "thumbnail_url": ""},
        {"caption": "Grilled chicken + quinoa = gains 💪 #cleaneating",
         "hashtags": ["healthy", "protein"], "thumbnail_url": ""},
    ],
    "italian": [
        {"caption": "Carbonara night 🍝 #pasta #italian #carbonara",
         "hashtags": ["pasta", "italian"], "thumbnail_url": ""},
        {"caption": "Homemade pizza is a religion #pizza #pizzanight",
         "hashtags": ["pizza", "homemade"], "thumbnail_url": ""},
        {"caption": "Tiramisu from scratch — worth every minute #tiramisu",
         "hashtags": ["tiramisu", "italian"], "thumbnail_url": ""},
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Action handlers — each takes a plain dict and returns a plain dict
# ─────────────────────────────────────────────────────────────────────────────

def _handle_analyze(data: dict) -> dict:
    """Scrape real Instagram / YouTube feed and run the craving pipeline."""
    alert = run_agent(
        username=data["username"],
        platform=data.get("platform", "instagram"),
        dietary=data.get("dietary", "all"),
        near_restaurant=data.get("near_restaurant", False),
        location=data.get("location", {"lat": 18.52, "lng": 73.85}),
    )
    return {"success": True, "result": alert, "username": data["username"]}


def _handle_analyze_mock(data: dict) -> dict:
    """Run the craving pipeline against caller-supplied posts (no scraping)."""
    from backend.nodes.personalization_memory import load_user_memory_node

    posts = data.get("posts", [])
    dietary = data.get("dietary", "all")
    near_restaurant = data.get("near_restaurant", False)
    time_context = data.get("time_context", "afternoon")
    location = data.get("location", {"lat": 18.52, "lng": 73.85})
    city = data.get("city", "Pune")

    base: FeedState = FeedState(
        username="mockuser", platform="instagram",
        posts=posts, food_detected=False,
        cuisine=None, specific_foods=[], is_snack=False,
        confidence=0.0, home_cookable=False,
        near_restaurant=near_restaurant, dietary=dietary,
        location=location, swiggy_mode=None, swiggy_result=None,
        alert_message=None, time_context=time_context,
        user_memory=None, user_preference_prompt="",
        skipped_restaurants=[], top_dishes=[], top_restaurants=[],
        ordered_dish=None, ordered_restaurant=None,
        order_channel=None, order_price_inr=None,
        order_cuisine=None, order_rating=None,
        skipped_restaurant=None, memory_saved=False,
        dish=None, city=city,
        price_comparison=None, price_comparison_text=None,
    )
    state = load_user_memory_node(base)
    s1 = analyze_food(state)

    if not s1["food_detected"] or not s1["cuisine"]:
        return {
            "success": True,
            "food_detected": False,
            "message": "No food cravings detected in these posts.",
            "analysis": None, "swiggy": None, "price_comparison": None,
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


def _handle_compare_prices(data: dict) -> dict:
    """Compare a dish price across Instamart, Food Delivery, and Dineout."""
    dish = data.get("dish", "")
    city = data.get("city", "Pune")
    if not dish:
        return {"success": False, "error": "'dish' is required"}

    dummy: dict[str, Any] = {"dish": dish, "city": city, "messages": []}
    result = price_comparison_node(dummy)
    return {
        "success": True,
        "dish": dish,
        "city": city,
        "comparison": result.get("price_comparison"),
        "summary": result.get("price_comparison_text"),
    }


def _handle_record_order(data: dict) -> dict:
    """Persist a confirmed order to user memory."""
    restaurant = data.get("restaurant", "")
    dish = data.get("dish", "")
    if not restaurant or not dish:
        return {"success": False, "error": "'restaurant' and 'dish' are required"}

    record_order(
        restaurant=restaurant,
        dish=dish,
        channel=data.get("channel", "food_delivery"),
        price=data.get("price"),
        cuisine=data.get("cuisine"),
        rating=data.get("rating"),
    )
    return {"success": True, "message": f"Order recorded: {dish} from {restaurant}"}


def _handle_skip(data: dict) -> dict:
    """Record that a restaurant suggestion was dismissed."""
    restaurant = data.get("restaurant", "")
    if not restaurant:
        return {"success": False, "error": "'restaurant' is required"}
    record_skip(restaurant)
    return {"success": True, "message": f"Skipped: {restaurant}"}


def _handle_rate_last_order(data: dict) -> dict:
    """Apply a 1-5 rating to the most recent order entry."""
    rating = data.get("rating")
    if rating is None:
        return {"success": False, "error": "'rating' (1-5) is required"}
    mem = UserMemory()
    mem.rate_last_order(int(rating))
    mem.save()
    return {"success": True, "rating_applied": int(rating)}


def _handle_get_memory(_data: dict) -> dict:
    """Return user preference / order history summary."""
    mem = UserMemory()
    return {
        "success": True,
        "summary": mem.summary_for_prompt(),
        "top_restaurants": mem.top_restaurants(10),
        "top_dishes": mem.top_dishes(10),
        "top_cuisines": mem.top_cuisines(5),
        "skipped_restaurants": mem.get_skipped_restaurants(),
        "order_history": mem.data.get("order_history", [])[-20:],
    }


def _handle_clear_memory(_data: dict) -> dict:
    """Wipe all stored user preferences."""
    if DEFAULT_MEMORY_FILE.exists():
        DEFAULT_MEMORY_FILE.unlink()
    return {"success": True, "message": "Memory cleared."}


def _handle_get_trends(_data: dict) -> dict:
    """Return craving trend data for the past 30 days."""
    trend_file = Path(_HERE) / "backend" / "craving_trends.json"
    if not trend_file.exists():
        return {"success": True, "trends": {}}
    with open(trend_file) as f:
        raw = json.load(f)
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    summary = {c: sum(1 for d in dates if d >= cutoff) for c, dates in raw.items()}
    summary = dict(sorted(summary.items(), key=lambda x: x[1], reverse=True))
    return {"success": True, "trends": summary, "raw": raw}


def _handle_get_demo_posts(data: dict) -> dict:
    """Return a preset batch of demo posts for testing."""
    preset = data.get("preset", "")
    posts = DEMO_POST_SETS.get(preset)
    if not posts:
        return {
            "success": False,
            "error": f"Unknown preset '{preset}'. Options: {list(DEMO_POST_SETS.keys())}",
        }
    return {"success": True, "preset": preset, "posts": posts}


# Map action name → handler function
_ACTION_HANDLERS = {
    "analyze":          _handle_analyze,
    "analyze_mock":     _handle_analyze_mock,
    "compare_prices":   _handle_compare_prices,
    "record_order":     _handle_record_order,
    "skip":             _handle_skip,
    "rate_last_order":  _handle_rate_last_order,
    "get_memory":       _handle_get_memory,
    "clear_memory":     _handle_clear_memory,
    "get_trends":       _handle_get_trends,
    "get_demo_posts":   _handle_get_demo_posts,
}


# ─────────────────────────────────────────────────────────────────────────────
# Conversation store (per-sender chat history for the LangChain fallback)
# ─────────────────────────────────────────────────────────────────────────────

CTX_HISTORY_TURNS = 10
CTX_IDLE_SECONDS = 60 * 60


class ConversationStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._convos: OrderedDict[str, list[BaseMessage]] = OrderedDict()
        self._last_seen: dict[str, float] = {}

    def get(self, ctx_id: str) -> list[BaseMessage]:
        with self._lock:
            return list(self._convos.get(ctx_id) or [])

    def append(self, ctx_id: str, human: str, ai: str) -> None:
        with self._lock:
            history = self._convos.get(ctx_id) or []
            history.append(HumanMessage(content=human))
            history.append(AIMessage(content=ai))
            cap = CTX_HISTORY_TURNS * 2
            if len(history) > cap:
                history = history[-cap:]
            self._convos[ctx_id] = history
            self._last_seen[ctx_id] = time.time()

    def gc(self) -> None:
        cutoff = time.time() - CTX_IDLE_SECONDS
        with self._lock:
            stale = [c for c, ts in self._last_seen.items() if ts < cutoff]
            for c in stale:
                self._convos.pop(c, None)
                self._last_seen.pop(c, None)


# ─────────────────────────────────────────────────────────────────────────────
# LangChain agent — used as fallback for natural-language queries,
# and also exposes all cravyo actions as callable tools so the LLM
# can chain them automatically.
# ─────────────────────────────────────────────────────────────────────────────

def build_langchain_agent(zynd_agent: ZyndAIAgent, registry_url: str) -> AgentExecutor:
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY"),
    )
    search = SearchAndDiscoveryManager(registry_url)
    a2a_client = A2AClient(
        keypair=zynd_agent.keypair,
        entity_id=zynd_agent.entity_id,
        fqan=_config.get("fqan"),
    )

    # ── Cravyo-specific tools ──────────────────────────────────────────────────

    @tool
    def analyze_feed(username: str, platform: str = "instagram",
                     dietary: str = "all", near_restaurant: bool = False) -> str:
        """Analyze a user's Instagram or YouTube feed for food cravings and
        return a Swiggy ordering suggestion.
        platform: 'instagram' or 'youtube'
        dietary: 'all' | 'veg' | 'non-veg' | 'gym' | 'diet' | 'vegan'
        """
        result = _handle_analyze({
            "username": username, "platform": platform,
            "dietary": dietary, "near_restaurant": near_restaurant,
        })
        return result.get("result", json.dumps(result))

    @tool
    def compare_prices(dish: str, city: str = "Pune") -> str:
        """Compare the price of a dish across Instamart, Food Delivery,
        and Dineout channels and return a cost breakdown."""
        result = _handle_compare_prices({"dish": dish, "city": city})
        return result.get("summary") or json.dumps(result)

    @tool
    def save_order(restaurant: str, dish: str, channel: str = "food_delivery",
                   price: float = None, cuisine: str = None, rating: int = None) -> str:
        """Record a confirmed food order into the user's preference memory
        so future suggestions are personalized."""
        result = _handle_record_order({
            "restaurant": restaurant, "dish": dish, "channel": channel,
            "price": price, "cuisine": cuisine, "rating": rating,
        })
        return result.get("message", json.dumps(result))

    @tool
    def skip_restaurant(restaurant: str) -> str:
        """Mark a restaurant as skipped. After 2 skips it stops appearing
        in suggestions."""
        result = _handle_skip({"restaurant": restaurant})
        return result.get("message", json.dumps(result))

    @tool
    def get_user_memory() -> str:
        """Return the user's order history, top cuisines, top restaurants,
        and personalization summary."""
        result = _handle_get_memory({})
        return json.dumps(result, indent=2)

    @tool
    def get_food_trends() -> str:
        """Return the user's craving trends for the past 30 days,
        ranked by cuisine frequency."""
        result = _handle_get_trends({})
        return json.dumps(result.get("trends", {}), indent=2)

    # ── Zynd network tools ────────────────────────────────────────────────────

    @tool
    def search_agents(query: str, limit: int = 5) -> str:
        """Search the Zynd registry for other agents by keyword."""
        results = search.search_agents_by_keyword(query, limit) or []
        return json.dumps(
            [
                {
                    "entity_id": r.get("entity_id"),
                    "name": r.get("name"),
                    "summary": r.get("summary"),
                    "entity_url": r.get("entity_url"),
                    "fqan": r.get("fqan"),
                    "tags": r.get("tags"),
                }
                for r in results
            ],
            indent=2,
        )

    @tool
    def call_agent(entity_url: str, message: str) -> str:
        """Send an A2A message to another agent on the Zynd network and
        return its reply. Pass the agent's card URL or base URL."""
        return a2a_client.ask(entity_url, message)

    tools = [
        analyze_feed,
        compare_prices,
        save_order,
        skip_restaurant,
        get_user_memory,
        get_food_trends,
        search_agents,
        call_agent,
    ]

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are Cravyo, an AI food assistant. "
                "You help users discover food cravings from their social media feeds, "
                "find restaurants, compare prices, and track order history. "
                "Use `analyze_feed` to check a user's Instagram/YouTube for food cravings. "
                "Use `compare_prices` to show price differences across channels. "
                "Use `save_order` after a user confirms an order. "
                "Use `get_user_memory` to show personalized preferences. "
                "Use `search_agents` and `call_agent` to delegate to specialist agents "
                "on the Zynd network when needed.",
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    return AgentExecutor(
        agent=create_tool_calling_agent(llm, tools, prompt),
        tools=tools,
        verbose=False,
        max_iterations=5,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    agent_config = AgentConfig(
        name=_config.get("name", "cravyo-agent"),
        description=_config.get(
            "description",
            "Cravyo — detects food cravings from Instagram/YouTube feeds and "
            "suggests nearby Swiggy orders with price comparison.",
        ),
        version=_config.get("version", "0.1.0"),
        category=_config.get("category", "food"),
        tags=_config.get("tags", ["food", "swiggy", "instagram", "cravings", "langgraph"]),
        server_host=_config.get("server_host", "0.0.0.0"),
        server_port=int(
            os.environ.get("ZYND_SERVER_PORT")
            or _config.get("server_port")
            or _config.get("webhook_port")
            or 5000
        ),
        auth_mode=_config.get("auth_mode", "permissive"),
        registry_url=resolve_registry_url(from_config_file=_config.get("registry_url")),
        keypair_path=os.environ.get("ZYND_AGENT_KEYPAIR_PATH", _config.get("keypair_path")),
        entity_url=os.environ.get("ZYND_ENTITY_URL", _config.get("entity_url")),
        price=_config.get("price"),
        entity_pricing=_config.get("entity_pricing"),
        entity_index=_config.get("entity_index", 0),
        skills=_config.get("skills"),
        fqan=_config.get("fqan"),
    )

    zynd_agent = ZyndAIAgent(
        config=agent_config,
        payload_model=RequestPayload,
        output_model=ResponsePayload,
        max_body_bytes=MAX_FILE_SIZE_BYTES,
    )

    # Build the LangChain executor (tools + Groq LLM)
    executor = build_langchain_agent(zynd_agent, agent_config.registry_url)

    # Conversation history store (per sender, GC'd every 5 min)
    conversations = ConversationStore()

    def _gc_loop() -> None:
        while True:
            time.sleep(5 * 60)
            try:
                conversations.gc()
            except Exception:
                pass

    threading.Thread(target=_gc_loop, daemon=True).start()

    # ── Master message handler ─────────────────────────────────────────────────
    def handle(handler_input: HandlerInput, task: TaskHandle) -> dict:
        """
        Route inbound A2A messages to the right cravyo action.

        Callers send JSON with an "action" field to invoke a specific
        capability directly (fast, deterministic).  Plain text falls
        through to the LangChain agent for conversational handling.
        """
        content: str = handler_input.message.content or ""
        ctx_id: str = handler_input.sender_entity_id or "anonymous"

        # ── Try JSON action dispatch first ─────────────────────────────────────
        # Two valid call styles:
        #   TextPart  → content is a JSON string  {"action": "...", ...}
        #   DataPart  → action comes in via payload (idiomatic A2A structured data)
        data: dict = {}
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            pass

        # DataPart fields land in handler_input.payload — merge them in so
        # callers can use either style and the handler routes identically.
        if isinstance(handler_input.payload, dict) and not data:
            data = handler_input.payload

        action = data.get("action") if isinstance(data, dict) else None

        if action:
            handler_fn = _ACTION_HANDLERS.get(action)
            if handler_fn:
                try:
                    return handler_fn(data)
                except Exception as exc:
                    return {"success": False, "error": str(exc), "action": action}
            else:
                return {
                    "success": False,
                    "error": f"Unknown action '{action}'. "
                             f"Available: {list(_ACTION_HANDLERS.keys())}",
                }

        # ── Natural-language fallback → LangChain agent ────────────────────────
        try:
            history = conversations.get(ctx_id)
            response = executor.invoke({"input": content, "chat_history": history})
            output: str = response.get("output", "")
            conversations.append(ctx_id, content, output)
            return {"response": output}
        except Exception as exc:
            return {"success": False, "error": f"Agent error: {exc}"}

    # Register handler and start
    zynd_agent.on_message(handle)
    zynd_agent.start()

    print(f"\nCravyo Agent is running")
    print(f"  A2A endpoint : {zynd_agent.a2a_url}")
    print(f"  Agent card   : {zynd_agent.card_url}")
    print(f"  Actions      : {list(_ACTION_HANDLERS.keys())}")
    print()

    if sys.stdin.isatty():
        print("Type 'exit' to quit\n")
        while True:
            try:
                cmd = input()
            except EOFError:
                break
            if cmd.lower() == "exit":
                break
        zynd_agent.stop()
    else:
        import signal
        signal.pause()
