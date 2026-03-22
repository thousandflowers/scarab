import typing
import aria2p
import os
import subprocess
import time
import logging

logger = logging.getLogger(__name__)

class Aria2Client:
    def __init__(self, host: str = "http://localhost", port: int = 6800, secret: str = ""):
        self.host = host
        self.port = port
        self.secret = secret
        self.api = aria2p.API(
            aria2p.Client(
                host=host,
                port=port,
                secret=secret
            )
        )
        
    def _is_running(self) -> bool:
        try:
            # Semplice heartbeat
            self.api.get_global_stat()
            return True
        except Exception:
            return False
            
    def ensure_running(self, download_dir: str):
        if self._is_running():
            return
            
        logger.info("Avvio aria2c in background...")
        os.makedirs(download_dir, exist_ok=True)
        
        args = [
            "aria2c",
            "--enable-rpc",
            f"--rpc-listen-port={self.port}",
            "--rpc-allow-origin-all",
            "--daemon=true",
            f"--dir={download_dir}",
            "--max-connection-per-server=4",
            "--split=4"
        ]
        if self.secret:
            args.append(f"--rpc-secret={self.secret}")
            
        subprocess.run(args, check=True)
        time.sleep(1) # wait for startup
        
    def add_download(self, url: str, filename: str = None, headers: dict = None) -> str:
        options = {}
        if filename:
            options["out"] = filename
            
        header_list = []
        if headers:
            for k, v in headers.items():
                if v:
                    header_list.append(f"{k}: {v}")
        if header_list:
            options["header"] = header_list
            
        download = self.api.add_uris([url], options=options)
        return download.gid
        
    def get_status(self, gid: str) -> dict:
        try:
            d = self.api.get_download(gid)
            return {
                "gid": d.gid,
                "status": d.status,
                "progress_pct": d.progress if d.total_length > 0 else 0,
                "download_speed_kbps": d.download_speed / 1024,
                "total_mb": d.total_length / (1024 * 1024) if d.total_length > 0 else 0,
                "completed_mb": d.completed_length / (1024 * 1024),
                "error_message": d.error_message
            }
        except Exception as e:
            return {"status": "error", "error_message": str(e)}
            
    def cancel(self, gid: str):
        try:
            d = self.api.get_download(gid)
            self.api.remove([d])
        except Exception:
            pass
