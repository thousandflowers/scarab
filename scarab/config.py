import tomllib
import tomli_w
from pathlib import Path

CONFIG_FILE = Path.home() / ".scarab" / "scarab.conf"
DEFAULTS = {
    "proxy": {
        "threshold_mb": 100,
        "auto_offload": True,
        "bypass_domains": "apple.com,icloud.com,whatsapp.com"
    },
    "notifications": {
        "ntfy_server": "https://ntfy.sh",
        "ntfy_topic": "",          # generated on first run
    },
    "delivery": {
        "mode": "filebrowser",     # filebrowser | mount | auto
    },
    "orchestrator": {
        "primary_node_url": "http://127.0.0.1:7800"
    },
    "downloader": {
        "local_downloads_dir": str(Path.home() / "Downloads" / "Scarab")
    }
}


def load() -> dict:
    if not CONFIG_FILE.exists():
        _write(DEFAULTS)
        return DEFAULTS
    with open(CONFIG_FILE, "rb") as f:
        return tomllib.load(f)


def get(key: str):
    """
    Dot-notation access: get("proxy.threshold_mb")
    """
    parts = key.split(".")
    data = load()
    for part in parts:
        data = data.get(part)
        if data is None:
            return None
    return data


def set(key: str, value):
    """
    Dot-notation write: set("proxy.threshold_mb", 200)
    Persists to scarab.conf immediately.
    """
    parts = key.split(".")
    data = load()
    node = data
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value
    _write(data)


def _write(data: dict):
    CONFIG_FILE.parent.mkdir(exist_ok=True)
    with open(CONFIG_FILE, "wb") as f:
        tomli_w.dump(data, f)

# Legacy compatibility methods during transition for other modules
def get_primary_node_url() -> str:
    return get("orchestrator.primary_node_url") or "http://127.0.0.1:7800"

def get_bypass_domains() -> list[str]:
    val = get("proxy.bypass_domains")
    if not val:
        return ["apple.com", "icloud.com", "whatsapp.com"]
    return [d.strip() for d in val.split(",") if d.strip()]

def get_proxy_port() -> int:
    return get("proxy.port") or 8080

def get_threshold_bytes() -> int:
    mb = get("proxy.threshold_mb") or 100
    return mb * 1024 * 1024

def is_auto_offload() -> bool:
    return bool(get("proxy.auto_offload"))

def get_local_downloads_dir() -> str:
    return get("downloader.local_downloads_dir") or str(Path.home() / "Downloads" / "Scarab")
