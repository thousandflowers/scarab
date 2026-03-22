import argparse
import subprocess
import signal
import sys
import logging
import os
from scarab.config import global_config
from scarab.core.proxy_manager import enable_system_proxy, disable_system_proxy
from scarab.setup import dependencies

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

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
        env = os.environ.copy()
        env["SCARAB_FORCE_CLI"] = "1"
        subprocess.Popen(["scarab", "start"], start_new_session=True, env=env)
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
    except FileNotFoundError:
        logger.error("mitmdump not found. Run 'pip install mitmproxy' inside the Scarab virtualenv.")
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
    
    # start / stop / misc
    subparsers.add_parser("start", help="Start the proxy")
    subparsers.add_parser("stop", help="Stop the proxy and restore network")
    subparsers.add_parser("mount", help="Mount server as network drive / open FileBrowser")
    subparsers.add_parser("connect", help="Connect client to server (fetch and install CA cert)")
    subparsers.add_parser("doctor", help="Run system diagnostics")
    
    # server subcommand
    server_parser = subparsers.add_parser("server", help="Server commands")
    server_sub = server_parser.add_subparsers(dest="server_cmd")
    mode_p = server_sub.add_parser("mode", help="Set the server runtime mode")
    mode_p.add_argument("mode_value", choices=["menubar", "background", "cli"])
    
    # config subcommand
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_sub = config_parser.add_subparsers(dest="config_cmd")
    get_p = config_sub.add_parser("get", help="Get a config value")
    get_p.add_argument("key")
    set_p = config_sub.add_parser("set", help="Set a config value")
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
        else:
            server_parser.print_help()
    elif args.command == "config":
        if args.config_cmd == "get":
            found = False
            for section in ("proxy", "orchestrator", "downloader", "notifier"):
                if global_config.parser.has_option(section, args.key):
                    print(global_config.parser.get(section, args.key))
                    found = True
                    break
            if not found:
                print(f"Key '{args.key}' not found in any section.")
        elif args.config_cmd == "set":
            # Intuitive section mapping for known keys
            section_map = {
                "primary_node_url": "orchestrator",
                "delivery": "orchestrator",
                "local_downloads_dir": "downloader",
                "ntfy_topic": "notifier",
                "ntfy_server": "notifier",
            }
            section = section_map.get(args.key, "proxy")
            global_config.update(section, args.key, args.value)
            print(f"Set [{section}] {args.key} = {args.value}")
        else:
            config_parser.print_help()
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
