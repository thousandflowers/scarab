import subprocess
import logging

logger = logging.getLogger(__name__)

def get_active_network_interface() -> str:
    """Returns the active network interface name (macOS only)."""
    # Default: Wi-Fi. Can be improved with networksetup -listnetworkserviceorder
    return "Wi-Fi"

def enable_system_proxy(port: int):
    """Registers Scarab as the system HTTP/HTTPS proxy on macOS."""
    interface = get_active_network_interface()
    logger.info(f"Setting system proxy on {interface} to 127.0.0.1:{port}...")
    subprocess.run(
        ["networksetup", "-setwebproxy", interface, "127.0.0.1", str(port)],
        check=False
    )
    subprocess.run(
        ["networksetup", "-setsecurewebproxy", interface, "127.0.0.1", str(port)],
        check=False
    )

def disable_system_proxy():
    """Removes Scarab as the system proxy on macOS."""
    interface = get_active_network_interface()
    logger.info(f"Removing system proxy on {interface}...")
    subprocess.run(
        ["networksetup", "-setwebproxystate", interface, "off"],
        check=False
    )
    subprocess.run(
        ["networksetup", "-setsecurewebproxystate", interface, "off"],
        check=False
    )
