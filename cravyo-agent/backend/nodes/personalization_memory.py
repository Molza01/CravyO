"""
Personalization Memory
======================
Persists user order history and preferences to a local JSON file
(`user_preferences.json`) that lives alongside `craving_trends.json`.

Two LangGraph nodes are provided:
    load_user_memory_node   – reads preferences at the start of a session
    save_user_memory_node   – updates preferences at the end of a session

A helper class `UserMemory` handles all file I/O and the preference logic.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MEMORY_FILE = Path(__file__).parent.parent / "user_preferences.json"

# How many times a user must skip a restaurant before we stop suggesting it
SKIP_THRESHOLD = 2

# ---------------------------------------------------------------------------
# UserMemory — the core data model
# ---------------------------------------------------------------------------


class UserMemory:
    """
    Manages a single JSON file with this shape:

    {
      "favourite_restaurants": {
        "<restaurant_name>": {
          "orders": <int>,
          "last_ordered": "<ISO date>",
          "dishes": ["<dish1>", ...],
          "score": <float>          # computed; higher = more preferred
        }
      },
      "skipped_restaurants": {
        "<restaurant_name>": {
          "skips": <int>,
          "last_skipped": "<ISO date>"
        }
      },
      "favourite_dishes": {
        "<dish_name>": <int>        # order count
      },
      "cuisine_preferences": {
        "<cuisine>": <int>
      },
      "order_history": [
        {
          "dish": "<str>",
          "restaurant": "<str>",
          "channel": "food_delivery | dineout | instamart",
          "price_inr": <number>,
          "timestamp": "<ISO datetime>",
          "rating": <int | null>    # 1-5 if user rated, else null
        }
      ],
      "last_updated": "<ISO datetime>"
    }
    """

    def __init__(self, filepath: str | Path = DEFAULT_MEMORY_FILE):
        self.filepath = Path(filepath)
        self._data: dict = {}
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = {}
        if not self._data:
            self._data = self._empty_schema()

    def save(self) -> None:
        self._data["last_updated"] = datetime.now().isoformat()
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _empty_schema() -> dict:
        return {
            "favourite_restaurants": {},
            "skipped_restaurants": {},
            "favourite_dishes": {},
            "cuisine_preferences": {},
            "order_history": [],
            "last_updated": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # Recording events
    # ------------------------------------------------------------------

    def record_order(
        self,
        dish: str,
        restaurant: str,
        channel: str = "food_delivery",
        price_inr: float | None = None,
        cuisine: str | None = None,
        rating: int | None = None,
    ) -> None:
        """Call this whenever the user places an order."""
        now = datetime.now()

        # Order history (keep last 200)
        entry = {
            "dish": dish,
            "restaurant": restaurant,
            "channel": channel,
            "price_inr": price_inr,
            "timestamp": now.isoformat(),
            "rating": rating,
        }
        self._data["order_history"].append(entry)
        if len(self._data["order_history"]) > 200:
            self._data["order_history"] = self._data["order_history"][-200:]

        # Favourite restaurants
        favs = self._data["favourite_restaurants"]
        if restaurant not in favs:
            favs[restaurant] = {"orders": 0, "last_ordered": None, "dishes": [], "score": 0.0}
        rec = favs[restaurant]
        rec["orders"] += 1
        rec["last_ordered"] = now.date().isoformat()
        if dish not in rec["dishes"]:
            rec["dishes"].append(dish)
        rec["score"] = self._compute_score(rec, rating)

        # Remove from skipped if they finally ordered
        self._data["skipped_restaurants"].pop(restaurant, None)

        # Favourite dishes
        dishes = self._data["favourite_dishes"]
        dishes[dish] = dishes.get(dish, 0) + 1

        # Cuisine preferences
        if cuisine:
            prefs = self._data["cuisine_preferences"]
            prefs[cuisine] = prefs.get(cuisine, 0) + 1

    def record_skip(self, restaurant: str) -> None:
        """Call this when the user dismisses / skips a suggestion."""
        skipped = self._data["skipped_restaurants"]
        if restaurant not in skipped:
            skipped[restaurant] = {"skips": 0, "last_skipped": None}
        skipped[restaurant]["skips"] += 1
        skipped[restaurant]["last_skipped"] = datetime.now().date().isoformat()

    def rate_last_order(self, rating: int) -> None:
        """Apply a 1-5 rating to the most recent order entry."""
        history = self._data["order_history"]
        if not history:
            return
        history[-1]["rating"] = max(1, min(5, rating))
        # Refresh restaurant score
        restaurant = history[-1]["restaurant"]
        favs = self._data["favourite_restaurants"]
        if restaurant in favs:
            favs[restaurant]["score"] = self._compute_score(favs[restaurant], rating)

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def should_skip(self, restaurant: str) -> bool:
        """Return True if we've skipped this restaurant too many times."""
        skip_data = self._data["skipped_restaurants"].get(restaurant, {})
        return skip_data.get("skips", 0) >= SKIP_THRESHOLD

    def top_restaurants(self, n: int = 5) -> list[str]:
        """Return the top-n preferred restaurants by score, excluding skipped ones."""
        favs = self._data["favourite_restaurants"]
        ranked = sorted(favs.items(), key=lambda kv: kv[1]["score"], reverse=True)
        return [name for name, _ in ranked if not self.should_skip(name)][:n]

    def top_dishes(self, n: int = 5) -> list[str]:
        """Return the top-n most-ordered dishes."""
        dishes = self._data["favourite_dishes"]
        return sorted(dishes, key=lambda d: dishes[d], reverse=True)[:n]

    def top_cuisines(self, n: int = 3) -> list[str]:
        """Return the top-n preferred cuisines."""
        prefs = self._data["cuisine_preferences"]
        return sorted(prefs, key=lambda c: prefs[c], reverse=True)[:n]

    def get_skipped_restaurants(self) -> list[str]:
        """Return all restaurants the user has skipped enough to suppress."""
        return [r for r, d in self._data["skipped_restaurants"].items()
                if d.get("skips", 0) >= SKIP_THRESHOLD]

    def summary_for_prompt(self) -> str:
        """
        Return a compact text block suitable for injecting into an LLM system
        prompt so the agent is automatically aware of user preferences.
        """
        top_r = self.top_restaurants(5)
        top_d = self.top_dishes(5)
        top_c = self.top_cuisines(3)
        skipped = self.get_skipped_restaurants()

        parts = []
        if top_r:
            parts.append(f"Favourite restaurants (in order): {', '.join(top_r)}")
        if top_d:
            parts.append(f"Most ordered dishes: {', '.join(top_d)}")
        if top_c:
            parts.append(f"Preferred cuisines: {', '.join(top_c)}")
        if skipped:
            parts.append(
                f"DO NOT suggest these restaurants (user repeatedly skipped them): {', '.join(skipped)}"
            )
        if not parts:
            return "No user preferences recorded yet."
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_score(rec: dict, latest_rating: int | None = None) -> float:
        """
        Simple score = order_count * base + average_rating_bonus.
        Recency is not factored in here but could be added.
        """
        base = rec.get("orders", 0) * 1.0
        if latest_rating:
            base += (latest_rating - 3) * 0.5  # -1 to +1 bonus
        return round(base, 2)

    # ------------------------------------------------------------------
    # Raw access (for debugging / testing)
    # ------------------------------------------------------------------

    @property
    def data(self) -> dict:
        return self._data


# ---------------------------------------------------------------------------
# LangGraph Nodes
# ---------------------------------------------------------------------------


def load_user_memory_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Node: Load user preferences at the start of a conversation.

    Reads `user_preferences.json`, injects a preference summary into
    state, and flags restaurants to avoid.

    Written state keys:
        user_memory            (UserMemory) – live object for other nodes to use
        user_preference_prompt (str)        – text block for the system prompt
        skipped_restaurants    (list[str])  – restaurants to filter out
        top_dishes             (list[str])
        top_restaurants        (list[str])
    """
    memory_path = state.get("memory_file", DEFAULT_MEMORY_FILE)
    mem = UserMemory(filepath=memory_path)

    return {
        **state,
        "user_memory": mem,
        "user_preference_prompt": mem.summary_for_prompt(),
        "skipped_restaurants": mem.get_skipped_restaurants(),
        "top_dishes": mem.top_dishes(5),
        "top_restaurants": mem.top_restaurants(5),
    }


def save_user_memory_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Node: Persist updated user preferences at the end of a conversation.

    Reads optional state keys written by earlier nodes:
        ordered_dish        (str)
        ordered_restaurant  (str)
        order_channel       (str)   default "food_delivery"
        order_price_inr     (float)
        order_cuisine       (str)
        order_rating        (int | None)
        skipped_restaurant  (str | list[str])

    If `user_memory` is not in state it re-loads from disk first.
    Always saves to disk at the end.
    """
    mem: UserMemory = state.get("user_memory") or UserMemory(
        filepath=state.get("memory_file", DEFAULT_MEMORY_FILE)
    )

    # Record an order if available
    dish = state.get("ordered_dish")
    restaurant = state.get("ordered_restaurant")
    if dish and restaurant:
        mem.record_order(
            dish=dish,
            restaurant=restaurant,
            channel=state.get("order_channel", "food_delivery"),
            price_inr=state.get("order_price_inr"),
            cuisine=state.get("order_cuisine"),
            rating=state.get("order_rating"),
        )

    # Record skips
    skipped = state.get("skipped_restaurant")
    if skipped:
        if isinstance(skipped, str):
            skipped = [skipped]
        for r in skipped:
            mem.record_skip(r)

    mem.save()

    return {
        **state,
        "user_memory": mem,
        "memory_saved": True,
    }
