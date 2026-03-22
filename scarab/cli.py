import argparse
import subprocess
import signal
import sys
import logging
import os
from scarab.config import global_config
from scarab.setup import dependencies

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
    from scarab.runtime.mode import get_mode
    mode = get_mode()
    if os.environ.get("SCARAB_FORCE_CLI") == "1":
        mode = "cli"
        
    if mode == "menubar":
        from scarab.runtime.menubar import run_menubar
        os.environ["SCARAB_FORCE_CLI"] = "1"
        import subprocess
        subprocess.Popen(["scarab", "start"], start_new_session=True, env=os.environ)
        run_menubar()
        return
    elif mode == "background":
        from scarab.runtime.background import run_background
        run_background()
        return
        
    dependencies.ensure_all()
    
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
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # start / stop
    subparsers.add_parser("start", help="Start the proxy")
    subparsers.add_parser("stop", help="Stop the proxy")
    subparsers.add_parser("mount", help="Mount server as network drive")
    subparsers.add_parser("connect", help="Connect client to server")
    subparsers.add_parser("doctor", help="Run system diagnostics")
    
    # server mode
    server_parser = subparsers.add_parser("server", help="Server commands")
    server_sub = server_parser.add_subparsers(dest="server_cmd")
    
    mode_p = server_sub.add_parser("mode")
    mode_p.add_argument("mode_value", choices=["menubar", "background", "cli"])
    
    # config
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_sub = config_parser.add_subparsers(dest="config_cmd")
    
    get_p = config_sub.add_parser("get")
    get_p.add_argument("key")
    
    set_p = config_sub.add_parser("set")
    set_p.add_argument("key")
    set_p.add_argument("value")
    
    args = parser.parse_args()
    
    if args.command == "start":
        start()
    elif args.command == "stop":
        stop()
    elif args.command == "doctor":
        from scarab.runtime.doctor import run_doctor
        run_doctor()
    elif args.command == "server":
        if args.server_cmd == "mode":
            from scarab.runtime.mode import set_mode
            set_mode(args.mode_value)
    elif args.command == "config":
        if args.config_cmd == "get":
            # Very basic get via reading scarab.conf directly (simplification)
            if global_config.parser.has_option("proxy", args.key):
                print(global_config.parser.get("proxy", args.key))
            elif global_config.parser.has_option("orchestrator", args.key):
                print(global_config.parser.get("orchestrator", args.key))
            elif global_config.parser.has_option("downloader", args.key):
                print(global_config.parser.get("downloader", args.key))
            else:
                print(f"Key {args.key} not found.")
        elif args.config_cmd == "set":
            # Map key to section intuitively for v0.1
            section = "proxy"
            if args.key in ["primary_node_url"]: section = "orchestrator"
            if args.key in ["local_downloads_dir"]: section = "downloader"
            if args.key in ["delivery"]: section = "orchestrator"
            
            global_config.update(section, args.key, args.value)
            print(f"Set {args.key} = {args.value} in section [{section}]")
    elif args.command == "mount":
        from scarab.transfer.netdrive import mount_drive
        mount_drive()
    elif args.command == "connect":
        from scarab.setup.cert_manager import fetch_and_trust_cert
        fetch_and_trust_cert()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
