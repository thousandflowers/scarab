import logging
import subprocess

logger = logging.getLogger(__name__)

def push_to_device(filename: str, target_ip: str):
    logger.info(f"Pushing {filename} to {target_ip} via Tailscale...")
    subprocess.run(["tailscale", "file", "cp", filename, f"{target_ip}:"], check=False)
