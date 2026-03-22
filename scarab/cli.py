import argparse
import subprocess
import signal
import sys
import logging
import os
from scarab.config import global_config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

def get_active_network_interface():
    # Per macOS default: Wi-Fi. 
    # TODO: renderlo dinamico con networksetup -listnetworkserviceorder
    return "Wi-Fi"

def enable_system_proxy(port: int):
    interface = get_active_network_interface()
    logger.info(f"Setting system proxy on {interface} to 127.0.0.1:{port}...")
    subprocess.run(["networksetup", "-setwebproxy", interface, "127.0.0.1", str(port)], check=False)
    subprocess.run(["networksetup", "-setsecurewebproxy", interface, "127.0.0.1", str(port)], check=False)

def disable_system_proxy():
    interface = get_active_network_interface()
    logger.info(f"Removing system proxy on {interface}...")
    subprocess.run(["networksetup", "-setwebproxystate", interface, "off"], check=False)
    subprocess.run(["networksetup", "-setsecurewebproxystate", interface, "off"], check=False)

def handle_exit(signum, frame):
    logger.info("\nShutting down Scarab...")
    disable_system_proxy()
    sys.exit(0)

def start():
    port = global_config.get_proxy_port()
    
    enable_system_proxy(port)
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    addon_path = os.path.join(os.path.dirname(__file__), "proxy", "addon.py")
    
    logger.info(f"Starting mitmdump on port {port}...")
    try:
        subprocess.run(["mitmdump", "-s", addon_path, "-p", str(port)])
    except Exception as e:
        logger.error(f"Error running mitmdump: {e}")
    finally:
        disable_system_proxy()

def stop():
    disable_system_proxy()
    logger.info("Proxy removed.")

def main():
    parser = argparse.ArgumentParser(description="Scarab CLI")
    parser.add_argument("command", choices=["start", "stop", "status", "jobs", "logs"], help="Command to run")
    
    args = parser.parse_args()
    
    if args.command == "start":
        start()
    elif args.command == "stop":
        stop()
    else:
        logger.info(f"Command '{args.command}' non ancora implementato in questa fase.")

if __name__ == "__main__":
    main()
