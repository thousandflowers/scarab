import logging
import subprocess
from scarab.config import global_config

logger = logging.getLogger(__name__)

def mount_drive():
    """Mounts the remote server or opens FileBrowser."""
    url = global_config.get_primary_node_url().replace(":7800", ":8080")
    logger.info(f"Accessing network drive / filebrowser at: {url}")
    try:
        subprocess.run(["open", url], check=False)
    except Exception:
        logger.info(f"Please open the URL manually: {url}")
