import logging
import shutil
import platform
import subprocess
from scarab.config import global_config

logger = logging.getLogger(__name__)

def run_doctor():
    logger.info("=== Scarab System Diagnostics ===")
    
    sys_os = platform.system()
    logger.info(f"OS: {sys_os}")
    
    if shutil.which("mitmdump"):
        logger.info("✅ mitmproxy is in PATH")
    else:
        logger.error("❌ mitmproxy NOT FOUND")
        
    if shutil.which("aria2c"):
        logger.info("✅ aria2c is installed")
    else:
        logger.error("❌ aria2c NOT FOUND")
        
    url = global_config.get_primary_node_url().replace("http://", "").replace(":7800", "")
    logger.info(f"Checking primary node ({url})...")
    try:
        if sys_os == "Windows":
            subprocess.run(["ping", "-n", "1", "-w", "1000", url], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            subprocess.run(["ping", "-c", "1", "-W", "1", url], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info(f"✅ Node {url} is pingable.")
    except Exception:
        logger.error(f"❌ Node {url} is UNREACHABLE. Please check your Tailscale connection.")
        
    logger.info("Diagnostics completed.")
