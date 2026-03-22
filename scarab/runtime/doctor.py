import logging
import shutil
import platform
import subprocess
from urllib.parse import urlparse
from scarab.config import global_config

logger = logging.getLogger(__name__)

def run_doctor():
    logger.info("=== Scarab System Diagnostics ===")
    
    sys_os = platform.system()
    logger.info(f"OS: {sys_os}")
    
    if shutil.which("mitmdump"):
        logger.info("✅ mitmproxy is in PATH")
    else:
        logger.error("❌ mitmproxy NOT FOUND — run: pip install mitmproxy")
        
    if shutil.which("aria2c"):
        logger.info("✅ aria2c is installed")
    else:
        logger.error("❌ aria2c NOT FOUND — on macOS run: brew install aria2")
        
    # Correctly parse the node URL regardless of port number
    raw_url = global_config.get_primary_node_url()
    parsed = urlparse(raw_url)
    host = parsed.hostname or "127.0.0.1"
    
    logger.info(f"Checking primary node reachability ({host})...")
    try:
        if sys_os == "Windows":
            subprocess.run(
                ["ping", "-n", "1", "-w", "1000", host],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        else:
            subprocess.run(
                ["ping", "-c", "1", "-W", "1", host],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        logger.info(f"✅ Node {host} is pingable.")
    except subprocess.CalledProcessError:
        logger.error(f"❌ Node {host} is UNREACHABLE. Check Tailscale is connected.")
    except Exception as e:
        logger.error(f"❌ Ping failed unexpectedly: {e}")
        
    logger.info("Diagnostics completed.")
