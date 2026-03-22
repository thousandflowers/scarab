import sys
import atexit
import signal
import click
import subprocess
import os

from scarab.setup.dependencies import ensure_aria2, start_aria2
from scarab.core.proxy_manager import enable_system_proxy, disable_system_proxy
from scarab.notifier.ntfy_client import get_topic
from scarab import config as cfg


@click.group()
def cli():
    """Scarab CLI - Intercept and offload large downloads."""
    pass


@cli.group()
def config():
    """Read and write Scarab configuration."""
    pass


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Set a config value. Example: scarab config set threshold 200"""
    try:
        value = int(value)
    except ValueError:
        try:
            value = float(value)
        except ValueError:
            pass  # keep as string

    cfg.set(f"proxy.{key}" if "." not in key else key, value)
    click.echo(f"[scarab] {key} = {value}")


@config.command("get")
@click.argument("key")
def config_get(key):
    """Get a config value. Example: scarab config get threshold"""
    value = cfg.get(f"proxy.{key}" if "." not in key else key)
    click.echo(f"[scarab] {key} = {value}")


@cli.command()
def start():
    """Start Scarab interceptor"""
    # 1. Install aria2 silently if not present
    if not ensure_aria2():
        print("[scarab] ❌ Could not start: aria2 unavailable.")
        sys.exit(1)

    # 2. Launch aria2 as child process
    aria2_proc = start_aria2()

    # 3. Always clean up on exit — crash or normal stop
    def cleanup(*_):
        aria2_proc.terminate()
        disable_system_proxy()
        sys.exit(0)

    atexit.register(cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT,  cleanup)

    # 4. Show ntfy topic so user knows where to subscribe
    print("[scarab] 🪲 Running")
    print(f"[scarab] Notifications topic: {get_topic()}")
    print("[scarab] Subscribe with the ntfy app to receive alerts")

    # 5. Start the proxy
    enable_system_proxy()
    port = cfg.get("proxy.port") or 8080
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    addon_path = os.path.join(script_dir, "proxy", "addon.py")

    try:
        subprocess.run([
            "mitmdump",
            "-s", addon_path,
            "-p", str(port),
            "--quiet"
        ])
    except KeyboardInterrupt:
        pass


@cli.command()
def stop():
    """Stop Scarab gracefully"""
    disable_system_proxy()
    click.echo("[scarab] Stopped proxy.")


@cli.command()
def status():
    """Show Scarab status and topic"""
    topic = get_topic()
    click.echo(f"Active topic: {topic}")


# Leave doctor untouched to prevent breaking diagnostics
@cli.command()
def doctor():
    """Run system diagnostics"""
    from scarab.runtime.doctor import run_doctor
    run_doctor()


if __name__ == "__main__":
    cli()
