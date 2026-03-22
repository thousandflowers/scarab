# scarab/notifier/ntfy_client.py
import httpx
import secrets
from scarab import config as cfg

def _get_or_create_topic() -> str:
    """
    Returns the ntfy topic, generating one if it doesn't exist yet.
    Topic format: scarab-XXXXXXXX (random, unique per installation)
    """
    topic = cfg.get("notifications.ntfy_topic")
    if not topic:
        topic = f"scarab-{secrets.token_urlsafe(8)}"
        cfg.set("notifications.ntfy_topic", topic)
    return topic

def notify(title: str, message: str, url: str = None):
    server = cfg.get("notifications.ntfy_server") or "https://ntfy.sh"
    topic  = _get_or_create_topic()

    headers = {
        "Title":    title,
        "Priority": "default",
        "Tags":     "beetle",
    }
    if url:
        headers["Click"] = url

    try:
        httpx.post(
            f"{server}/{topic}".replace("sh//", "sh/"), # quick fix just in case
            content=message.encode("utf-8"),
            headers=headers,
            timeout=5,
        )
    except Exception:
        pass  # notifications must never block the download flow

def notify_started(filename: str, size_mb: float):
    notify(
        title="🪲 Download started",
        message=f"{filename} ({size_mb:.0f} MB)",
    )

def notify_complete(filename: str, duration_sec: int, dest_url: str = None):
    mins    = duration_sec // 60
    secs    = duration_sec % 60
    elapsed = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
    notify(
        title="✅ Ready",
        message=f"{filename} — {elapsed}",
        url=dest_url,
    )

def notify_error(filename: str, reason: str):
    notify(
        title="❌ Download failed",
        message=f"{filename} — {reason}",
    )

def notify_fallback(filename: str):
    notify(
        title="⚠️ Server unavailable",
        message=f"{filename} — downloading locally instead",
    )

def get_topic() -> str:
    """Returns the topic for display in `scarab status`."""
    return _get_or_create_topic()
