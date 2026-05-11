import logging
import os
import sys
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Callable

try:
    from win10toast import ToastNotifier
    _WIN32 = True
except Exception:
    _WIN32 = False


logger = logging.getLogger("notification")


class NotificationBackend(ABC):
    @abstractmethod
    def send(self, title: str, message: str, urgency: str = "medium") -> bool:
        raise NotImplementedError


class DesktopBackend(NotificationBackend):
    def __init__(self) -> None:
        self._toaster: ToastNotifier | None = None
        if _WIN32:
            try:
                self._toaster = ToastNotifier()
            except Exception as e:
                logger.warning("Win10Toaster unavailable: %s", e)

    def send(self, title: str, message: str, urgency: str = "medium") -> bool:
        if self._toaster:
            try:
                self._toaster.show_toast(
                    title=title,
                    msg=message,
                    duration=5,
                    threaded=True,
                )
                return True
            except Exception as e:
                logger.error("Desktop notification failed: %s", e)
        return False


class LogBackend(NotificationBackend):
    def send(self, title: str, message: str, urgency: str = "medium") -> bool:
        logger.info("[%s] %s | %s", urgency.upper(), title, message)
        return True


class WebhookBackend(NotificationBackend):
    def __init__(self, url: str | None = None) -> None:
        self._url = url or os.getenv("NOTIFICATION_WEBHOOK_URL", "")

    def send(self, title: str, message: str, urgency: str = "medium") -> bool:
        if not self._url:
            return False
        try:
            import requests
            payload = {
                "title": title,
                "message": message,
                "urgency": urgency,
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            r = requests.post(self._url, json=payload, timeout=5)
            return r.status_code < 400
        except Exception as e:
            logger.error("Webhook notification failed: %s", e)
            return False


def _resolve_backend() -> NotificationBackend:
    mode = os.getenv("NOTIFICATION_MODE", "desktop").lower()
    if mode == "desktop":
        if _WIN32:
            return DesktopBackend()
        return LogBackend()
    if mode == "webhook":
        return WebhookBackend()
    return LogBackend()


_backends: dict[str, NotificationBackend] = {}
_backends_lock = threading.Lock()


def _get_backend(name: str = "default") -> NotificationBackend:
    with _backends_lock:
        if name not in _backends:
            _backends[name] = _resolve_backend()
        return _backends[name]


def send_notification(
    message: str,
    title: str = "Cravyo Agent",
    urgency: str = "medium",
    backend: str = "default",
) -> bool:
    return _get_backend(backend).send(title, message, urgency)


class CravingScheduler:
    def __init__(
        self,
        check_interval_mins: int = 30,
    ) -> None:
        self._interval = check_interval_mins * 60
        self._running = False
        self._thread: threading.Thread | None = None
        self._task: Callable[[], None] | None = None

    def _loop(self) -> None:
        while self._running:
            try:
                if self._task:
                    self._task()
            except Exception as e:
                logger.error("Scheduled task error: %s", e)
            time.sleep(self._interval)

    def start(self, task: Callable[[], None]) -> None:
        if self._running:
            return
        self._task = task
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info(
            "Scheduler started (interval=%ds, task=%s)",
            self._interval,
            getattr(task, "__name__", repr(task)),
        )

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Scheduler stopped")

    @property
    def is_running(self) -> bool:
        return self._running


def get_meal_time_tasks() -> list[dict]:
    return [
        {"name": "breakfast", "hour": 8, "minute": 0},
        {"name": "lunch", "hour": 13, "minute": 0},
        {"name": "evening_snacks", "hour": 18, "minute": 0},
        {"name": "dinner", "hour": 20, "minute": 0},
    ]