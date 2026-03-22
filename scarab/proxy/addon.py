import asyncio
import logging
from mitmproxy import http, ctx
from typing import Dict, Any

from scarab.proxy.inspector import Inspector, OffloadDecision
from scarab.config import global_config
from scarab.core.remote_handler import handle_offload
from scarab.core.sleep_handler import sleep_detector
from scarab.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class ScarabAddon:
    def __init__(self):
        self.inspector = Inspector()
        
    def load(self, loader):
        """Converte la bypass_domains in ignore_hosts proxy-level"""
        bypass_domains = global_config.get_bypass_domains()
        # Build regex patterns without backslash inside f-string (invalid on Python < 3.12)
        escaped = [domain.replace(".", r"\.") for domain in bypass_domains]
        ignore_hosts = [f"^{d}.*" for d in escaped]
        ctx.options.ignore_hosts = tuple(ignore_hosts)
        
        # Schedule the sleep detector as an asyncio task.
        # mitmproxy's load() is sync but runs inside an already-running loop,
        # so we get the running loop and schedule the coroutine on it.
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

    def _extract_metadata(self, flow: http.HTTPFlow) -> Dict[str, Any]:
        req_headers = flow.request.headers
        return {
            "url": flow.request.url,
            "cookie": req_headers.get("Cookie", ""),
            "user_agent": req_headers.get("User-Agent", ""),
            "authorization": req_headers.get("Authorization", ""),
            "method": flow.request.method,
        }

    async def responseheaders(self, flow: http.HTTPFlow):
        """Intercettiamo la risposta appena ricevuti gli header, PRIMA di scaricare il body."""
        request_url = flow.request.url
        decision, size, filename = self.inspector.inspect_response(flow.response, request_url)
        
        if decision == OffloadDecision.PASSTHROUGH:
            # Lascia scaricare in streaming per evitare di occupare RAM per file tollerabili
            flow.response.stream = True
            return
            
        do_offload = False
        if decision == OffloadDecision.OFFLOAD:
            do_offload = True
        elif decision == OffloadDecision.ASK:
            do_offload = await self._ask_user(filename, size)
            
        if do_offload:
            metadata = self._extract_metadata(flow)
            ctx.log.warning(f"🚀 [SCARAB] Offloading {filename} ({size} bytes). Metadata extracted.")
            
            # Inseriamo un payload custom e blocchiamo il download originale qui
            flow.response.status_code = 403
            flow.response.headers["Content-Type"] = "text/html"
            flow.response.stream = False # Non mandare in streaming questa finta
            flow.response.content = b"<html><body><h1>Scarab Interceptor</h1><p>Il file &egrave; stato instradato a Scarab e arriver&agrave; a breve!</p></body></html>"
            
            # Invio al nodo remoto (Orchestrator) predefinito o fallback locale
            headers_dict = {
                "Cookie": metadata["cookie"],
                "User-Agent": metadata["user_agent"],
                "Authorization": metadata["authorization"]
            }
            asyncio.create_task(handle_offload(metadata["url"], filename, headers_dict, size))
        else:
            # L'utente ha rifiutato l'offload, il file prosegue normalmente in streaming
            flow.response.stream = True

addons = [ScarabAddon()]
