import configparser
import os
from pathlib import Path

# Config defaults
DEFAULT_PORT = 8080
DEFAULT_THRESHOLD_MB = 100
DEFAULT_AUTO_OFFLOAD = False
DEFAULT_BYPASS_DOMAINS = ["apple.com", "icloud.com", "whatsapp.com"]

class Config:
    def __init__(self, config_path: str = "scarab.conf"):
        self.config_path = config_path
        self.parser = configparser.ConfigParser()
        self.load()

    def load(self):
        if os.path.exists(self.config_path):
            self.parser.read(self.config_path)

    def update(self, section: str, key: str, value: str):
        if not self.parser.has_section(section):
            self.parser.add_section(section)
        self.parser.set(section, key, str(value))
        with open(self.config_path, "w") as f:
            self.parser.write(f)

    def get_proxy_port(self) -> int:
        return self.parser.getint("proxy", "port", fallback=DEFAULT_PORT)

    def get_threshold_mb(self) -> int:
        return self.parser.getint("proxy", "threshold_mb", fallback=DEFAULT_THRESHOLD_MB)

    def get_threshold_bytes(self) -> int:
        return self.get_threshold_mb() * 1024 * 1024

    def is_auto_offload(self) -> bool:
        return self.parser.getboolean("proxy", "auto_offload", fallback=DEFAULT_AUTO_OFFLOAD)

    def get_bypass_domains(self) -> list[str]:
        val = self.parser.get("proxy", "bypass_domains", fallback=None)
        if val is None:
            return DEFAULT_BYPASS_DOMAINS
        return [d.strip() for d in val.split(",") if d.strip()]

    def get_primary_node_url(self) -> str:
        return self.parser.get("orchestrator", "primary_node_url", fallback="http://127.0.0.1:7800")
        
    def get_local_downloads_dir(self) -> str:
        default_dir = str(Path.home() / "Downloads" / "Scarab")
        path = self.parser.get("downloader", "local_downloads_dir", fallback=default_dir)
        return os.path.expanduser(path)

    def get_ntfy_topic(self) -> str:
        return self.parser.get("notifier", "ntfy_topic", fallback="scarab_alerts")

    def get_ntfy_server(self) -> str:
        return self.parser.get("notifier", "ntfy_server", fallback="https://ntfy.sh")

global_config = Config()
