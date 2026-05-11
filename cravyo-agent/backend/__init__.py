"""
cravyo-agent backend package.

Re-exports the public API so agent.py can do:
    from backend import run_agent, record_order, record_skip, ...
"""

from .feed_analyzer_agent import (
    run_agent,
    record_order,
    record_skip,
    analyze_food,
    decide_swiggy_mode,
    call_swiggy,
    FeedState,
)
from .nodes.price_comparison_node import price_comparison_node
from .nodes.personalization_memory import UserMemory, DEFAULT_MEMORY_FILE
from .fusion_engine import fusion_engine
from .meal_nudge_engine import get_meal_nudge
from .notification import send_notification, CravingScheduler, get_meal_time_tasks

__all__ = [
    "run_agent",
    "record_order",
    "record_skip",
    "analyze_food",
    "decide_swiggy_mode",
    "call_swiggy",
    "FeedState",
    "price_comparison_node",
    "UserMemory",
    "DEFAULT_MEMORY_FILE",
    "fusion_engine",
    "get_meal_nudge",
    "send_notification",
    "CravingScheduler",
    "get_meal_time_tasks",
]
