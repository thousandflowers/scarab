import re
from enum import Enum
from typing import Optional, Tuple
from mitmproxy import http
from scarab.config import global_config

class OffloadDecision(Enum):
    PASSTHROUGH = "passthrough"
    OFFLOAD = "offload"
    ASK = "ask"

class Inspector:
    """
    Legge gli header HTTP e determina la OffloadDecision.
    """
    
    def __init__(self):
        # Media types that we might want to intercept even if chunked (e.g. unknown size video/archives)
        self.interceptable_types = [
            "application/zip", "application/x-zip-compressed", "application/x-rar-compressed",
            "application/x-7z-compressed", "application/x-tar", "application/gzip",
            "application/octet-stream", "application/x-apple-diskimage", "application/x-iso9660-image",
            "video/mp4", "video/x-matroska", "video/webm", "video/quicktime"
        ]

    def _get_filename_from_cd(self, cd: str) -> Optional[str]:
        """Estrae il filename dal Content-Disposition."""
        if not cd:
            return None
        # Prova filename="..." oppure filename=...
        match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^\"]+)"?', cd, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _extract_filename(self, response: http.Response, request_url: str) -> str:
        cd = response.headers.get("Content-Disposition")
        fname = self._get_filename_from_cd(cd) if cd else None
        if fname:
            return fname
        
        # Fallback on URL path
        path = re.sub(r'\?.*$', '', request_url)
        return path.split("/")[-1] or "downloaded_file"

    def inspect_response(self, response: http.Response, request_url: str) -> Tuple[OffloadDecision, Optional[int], str]:
        """
        Ritorna:
        - La decisione (PASSTHROUGH, OFFLOAD, ASK)
        - Content Length in bytes (se nota)
        - Nome del file (estratto da header o URL)
        """
        content_length_str = response.headers.get("Content-Length")
        content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
        transfer_encoding = response.headers.get("Transfer-Encoding", "").lower()
        
        filename = self._extract_filename(response, request_url)
        threshold_bytes = global_config.get_threshold_bytes()

        is_chunked = "chunked" in transfer_encoding
        is_interceptable = content_type in self.interceptable_types or "application/" in content_type or "video/" in content_type
        
        # 1. Size conosciuta
        if content_length_str and content_length_str.isdigit():
            size = int(content_length_str)
            if size > threshold_bytes:
                decision = OffloadDecision.OFFLOAD if global_config.is_auto_offload() else OffloadDecision.ASK
                return decision, size, filename
            else:
                return OffloadDecision.PASSTHROUGH, size, filename
        
        # 2. Size sconosciuta (Chunked)
        if is_chunked and is_interceptable:
            # Non sappiamo quanto è grande, ma è un archivio/media. Chiediamo all'utente.
            return OffloadDecision.ASK, None, filename

        # Default fallback
        return OffloadDecision.PASSTHROUGH, None, filename
