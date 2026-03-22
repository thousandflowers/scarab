import asyncio
import logging
import threading
import time
from mitmproxy import http, ctx

from scarab.proxy.inspector import Inspector, OffloadDecision
from scarab import config as cfg
from scarab.core.sleep_handler import sleep_detector
from scarab.logger import setup_logging
from scarab.downloader.aria2_client import add_download, wait_for_completion
from scarab.notifier.ntfy_client import (
    notify_started, notify_complete, notify_error, notify_fallback
)

setup_logging()
logger = logging.getLogger(__name__)

RETRY_SECONDS = 30

def offload(url: str, filename: str, size_bytes: int):
    """
    Offloads a download to aria2.
    Runs in a separate thread so the proxy stays responsive.

    Fallback logic:
    - Tries to reach aria2 for up to RETRY_SECONDS
    - If unreachable: sends a single notification, lets download proceed normally
    - Never blocks the user
    """
    def run():
        size_mb = size_bytes / 1_000_000
        start   = time.time()

        # Check aria2 is reachable before killing the browser download
        if not _wait_for_aria2(RETRY_SECONDS):
            notify_fallback(filename)
            # Do not kill the flow — let the browser download normally
            return

        try:
            notify_started(filename, size_mb)
            print(f"\n[scarab] 🪲 {filename} ({size_mb:.0f} MB)")

            gid = add_download(url, filename=filename)

            def show_progress(job):
                filled = int(job.progress_pct / 5)
                bar    = "█" * filled + "░" * (20 - filled)
                print(
                    f"\r[scarab] [{bar}] "
                    f"{job.progress_pct:.1f}% "
                    f"@ {job.speed_mbps:.1f} MB/s",
                    end="", flush=True,
                )

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                wait_for_completion(gid, on_progress=show_progress)
            )

            duration = int(time.time() - start)
            print(f"\n[scarab] ✅ {filename} — done in {duration}s")
            notify_complete(filename, duration)

        except Exception as e:
            print(f"\n[scarab] ❌ {filename}: {e}")
            notify_error(filename, str(e))

    threading.Thread(target=run, daemon=True).start()

def _wait_for_aria2(timeout_sec: int) -> bool:
    """
    Waits up to timeout_sec for aria2 to be reachable.
    Returns True if aria2 responds, False if timeout exceeded.
    """
    import httpx
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            httpx.get("http://localhost:6800/jsonrpc", timeout=2)
            return True
        except Exception:
            time.sleep(2)
    return False

class ScarabAddon:
    def __init__(self):
        self.inspector = Inspector()
        
    def load(self, loader):
        """Converte la bypass_domains in ignore_hosts proxy-level"""
        val = cfg.get("proxy.bypass_domains")
        if not val:
            bypass_domains = ["apple.com", "icloud.com", "whatsapp.com"]
        else:
            bypass_domains = [d.strip() for d in val.split(",") if d.strip()]
            
        escaped = [domain.replace(".", r"\.") for domain in bypass_domains]
        ignore_hosts = [f"^{d}.*" for d in escaped]
        ctx.options.ignore_hosts = tuple(ignore_hosts)
        
        # Schedule the sleep detector as an asyncio task
        loop = asyncio.get_event_loop()
        loop.create_task(sleep_detector())

    async def _ask_user(self, filename: str, size: int) -> bool:
        """Mostra un popup all'utente su macOS per chiedere se offlodare."""
        if size:
            size_str = f"{size / (1024*1024):.1f} MB"
        else:
            size_str = "Dimensione ignota (Chunked/Stream)"
            
        script = f'''
        display dialog "Il file '{filename}' ({size_str}) sta per essere scaricato.\\nVuoi scaricarlo tramite Scarab sul Raspberry Pi?" buttons {{"No, scarica qui", "Sì, offload"}} default button "Sì, offload" with title "Scarab Interceptor"
        '''
        proc = await asyncio.create_subprocess_exec(
            "osascript", "-e", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode("utf-8").strip()
        
        if "button returned:Sì, offload" in output:
            return True
        return False

    async def responseheaders(self, flow: http.HTTPFlow):
        """Intercettiamo la risposta appena ricevuti gli header."""
        request_url = flow.request.url
        decision, size, filename = self.inspector.inspect_response(flow.response, request_url)
        
        if decision == OffloadDecision.PASSTHROUGH:
            flow.response.stream = True
            return
            
        do_offload = False
        if decision == OffloadDecision.OFFLOAD:
            do_offload = True
        elif decision == OffloadDecision.ASK:
            do_offload = await self._ask_user(filename, size)
            
        if do_offload:
            # Scarab Phase 2 implementation:
            # We don't change the request blocking right away unless aria2 is up.
            # `offload` manages the verification. Actually, `PHASE_2.md` specifies
            # that we must call offload and then flow.kill() ONLY if aria2 is reachable.
            # Since `offload` runs in a thread and checks reachability, we must block here.
            
            # To strictly follow PHASE_2.md:
            if _wait_for_aria2(2):  # Quick check before killing
                offload(flow.request.pretty_url, filename, size)
                flow.kill()
            else:
                notify_fallback(filename)
                flow.response.stream = True
        else:
            flow.response.stream = True

addons = [ScarabAddon()]
