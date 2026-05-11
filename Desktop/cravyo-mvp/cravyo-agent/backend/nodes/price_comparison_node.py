"""
Price Comparison Node
=====================
Compares the cost of the same dish across three channels:
  - Instamart (grocery / quick-commerce)
  - Food Delivery (Swiggy / Zomato style)
  - Dineout (restaurant table pricing)

The node enriches the agent state with a `price_comparison` key
that downstream nodes or the final response formatter can display.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import AIMessage
from langchain_groq import ChatGroq

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

COMPARISON_PROMPT = """
You are a smart food-price analyst for Indian cities.

Given the dish "{dish}" in the city "{city}", produce a realistic price
comparison across three purchase channels.

Return ONLY a valid JSON object — no markdown, no extra text — with this schema:

{{
  "dish": "<string>",
  "city": "<string>",
  "channels": {{
    "instamart": {{
      "label": "Instamart (cook at home)",
      "item": "<what to buy, e.g. 'Frozen Biryani 500g pack'>",
      "price_inr": <number>,
      "delivery_time_min": <number>,
      "delivery_fee_inr": <number>,
      "total_inr": <number>,
      "serves": <number>,
      "cost_per_serving_inr": <number>,
      "pros": ["<string>", "<string>"],
      "cons": ["<string>"]
    }},
    "food_delivery": {{
      "label": "Food Delivery (Swiggy / Zomato)",
      "restaurant": "<example restaurant name>",
      "price_inr": <number>,
      "delivery_time_min": <number>,
      "delivery_fee_inr": <number>,
      "platform_fee_inr": <number>,
      "total_inr": <number>,
      "serves": 1,
      "cost_per_serving_inr": <number>,
      "pros": ["<string>", "<string>"],
      "cons": ["<string>"]
    }},
    "dineout": {{
      "label": "Dine Out (restaurant)",
      "restaurant": "<example restaurant name>",
      "price_inr": <number>,
      "service_charge_pct": <number>,
      "gst_pct": <number>,
      "total_inr": <number>,
      "serves": 1,
      "cost_per_serving_inr": <number>,
      "travel_time_min": <number>,
      "pros": ["<string>", "<string>"],
      "cons": ["<string>"]
    }}
  }},
  "recommendation": {{
    "budget_pick": "instamart | food_delivery | dineout",
    "fastest_pick": "instamart | food_delivery | dineout",
    "experience_pick": "instamart | food_delivery | dineout",
    "summary": "<one sentence>"
  }}
}}
"""


def _extract_json(text: str) -> dict:
    """Robustly extract the first JSON object from an LLM response."""
    text = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise


# ---------------------------------------------------------------------------
# Table formatter
# ---------------------------------------------------------------------------

# Emojis are 2 visual chars wide; Python len() counts them as 1.
# This map lets us compensate padding so terminal columns stay aligned.
_EMOJI_EXTRA: dict[str, int] = {
    "🛒": 1, "🛵": 1, "🍽": 1,
    "✅": 1, "⚠": 0, "💸": 1, "⚡": 1, "🌟": 1, "📌": 1,
}

def _pad(text: str, width: int, align: str = "<") -> str:
    """Like f'{text:<width}' but compensates for emoji visual width."""
    extra = sum(v for k, v in _EMOJI_EXTRA.items() if k in text)
    adjusted = width - extra
    if align == "<":
        return text.ljust(adjusted)
    if align == ">":
        return text.rjust(adjusted)
    return text.center(adjusted)


_FULL  = "─" * 72
_THICK = "═" * 72

CHANNEL_ICON = {"instamart": "🛒", "food_delivery": "🛵", "dineout": "🍽️"}
CHANNEL_ORDER = ["instamart", "food_delivery", "dineout"]


def _format_comparison_table(data: dict) -> str:
    channels = data.get("channels", {})
    dish = data.get("dish", "?")
    city = data.get("city", "?")

    lines = [
        "",
        _THICK,
        f"  💰  PRICE COMPARISON — {dish.title()} in {city}",
        _THICK,
        "",
    ]

    # ── Main table ────────────────────────────────────────────────────────────
    col_ch   = 30   # channel label
    col_item = 28   # item / restaurant
    col_base =  8   # base price
    col_fee  =  6   # delivery / service fee
    col_tot  =  9   # total
    col_time =  8   # time

    header = (
        f"  {_pad('Channel', col_ch)}"
        f"  {_pad('What You Get', col_item)}"
        f"  {'Base':>{col_base}}"
        f"  {'Fee':>{col_fee}}"
        f"  {'Total':>{col_tot}}"
        f"  {'Time':>{col_time}}"
    )
    lines += [header, "  " + _FULL]

    best_total = None
    cheapest_key = None
    for key in CHANNEL_ORDER:
        ch = channels.get(key, {})
        t = ch.get("total_inr")
        if t and (best_total is None or t < best_total):
            best_total = t
            cheapest_key = key

    for key in CHANNEL_ORDER:
        ch = channels.get(key, {})
        if not ch:
            continue

        icon  = CHANNEL_ICON[key]
        label = icon + " " + ch.get("label", key)
        item  = (ch.get("item") or ch.get("restaurant") or "—")[:col_item]

        base  = f"₹{ch.get('price_inr', '?')}"
        if key == "instamart":
            fee = f"₹{ch.get('delivery_fee_inr', 0)}"
        elif key == "food_delivery":
            fee = f"₹{ch.get('delivery_fee_inr', 0) + ch.get('platform_fee_inr', 0)}"
        else:  # dineout
            sc  = ch.get("service_charge_pct", 0)
            gst = ch.get("gst_pct", 0)
            fee = f"{sc + gst:.0f}%"

        total = f"₹{ch.get('total_inr', '?')}"
        if key == cheapest_key:
            total += " 💸"

        if key == "dineout":
            time_val = ch.get("travel_time_min", "?")
            time_ = f"{time_val}m walk"
        else:
            time_val = ch.get("delivery_time_min", "?")
            time_ = f"{time_val} min"

        row = (
            f"  {_pad(label, col_ch)}"
            f"  {_pad(item, col_item)}"
            f"  {base:>{col_base}}"
            f"  {fee:>{col_fee}}"
            f"  {_pad(total, col_tot, '>')}"
            f"  {time_:>{col_time}}"
        )
        lines.append(row)

        # Per-serving sub-row when serves > 1
        serves = ch.get("serves", 1)
        if serves and int(serves) > 1:
            cps = ch.get("cost_per_serving_inr")
            if cps:
                lines.append(
                    f"  {_pad('', col_ch)}"
                    f"  {_pad(f'  → {serves} servings · ₹{cps}/serving', col_item + col_base + col_fee + 4)}"
                )

    lines.append("  " + _FULL)

    # ── Pros / Cons ───────────────────────────────────────────────────────────
    lines += ["", "  Details per channel:", ""]
    for key in CHANNEL_ORDER:
        ch = channels.get(key, {})
        if not ch:
            continue
        icon  = CHANNEL_ICON[key]
        label = ch.get("label", key)
        pros  = ch.get("pros", [])
        cons  = ch.get("cons", [])
        lines.append(f"  {icon}  {label}")
        for p in pros[:2]:
            lines.append(f"       ✅ {p}")
        for c in cons[:1]:
            lines.append(f"       ⚠  {c}")
        lines.append("")

    # ── Recommendation ────────────────────────────────────────────────────────
    rec = data.get("recommendation", {})
    _pick_label = {"instamart": "🛒 Instamart", "food_delivery": "🛵 Food Delivery", "dineout": "🍽️  Dineout"}
    lines += [
        "  " + _FULL,
        "  📌  Quick Picks:",
        f"    💸  Budget      →  {_pick_label.get(rec.get('budget_pick','?'), rec.get('budget_pick','?'))}",
        f"    ⚡  Fastest     →  {_pick_label.get(rec.get('fastest_pick','?'), rec.get('fastest_pick','?'))}",
        f"    🌟  Experience  →  {_pick_label.get(rec.get('experience_pick','?'), rec.get('experience_pick','?'))}",
        "",
        f"  {rec.get('summary', '')}",
        "  " + _THICK,
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------


def price_comparison_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node.

    Reads `state["dish"]` and `state["city"]` (with sensible defaults),
    calls the LLM to generate a structured price comparison, and stores
    both the raw dict and a formatted string back into state.

    Expected state keys (inputs):
        dish (str)  – e.g. "Chicken Biryani"
        city (str)  – e.g. "Mumbai"

    Written state keys (outputs):
        price_comparison      (dict)  – full structured data
        price_comparison_text (str)   – human-readable summary
        messages              (list)  – appends an AIMessage
    """
    dish = state.get("dish") or state.get("craving") or "the requested dish"
    city = state.get("city") or "your city"

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)

    prompt = COMPARISON_PROMPT.format(dish=dish, city=city)
    response = llm.invoke(prompt)
    raw_text = response.content

    try:
        comparison_data = _extract_json(raw_text)
    except Exception as exc:
        comparison_data = {"error": str(exc), "raw": raw_text}

    formatted = (
        _format_comparison_table(comparison_data)
        if "channels" in comparison_data
        else raw_text
    )

    messages = list(state.get("messages", []))
    messages.append(AIMessage(content=formatted))

    return {
        **state,
        "price_comparison":      comparison_data,
        "price_comparison_text": formatted,
        "messages":              messages,
    }
