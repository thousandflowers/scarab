import httpx
import logging
from typing import Union

logger = logging.getLogger(__name__)

class NtfyClient:
    def __init__(self, server: str, topic: str):
        # Assicuriamoci che l'URL base non finisca con /
        self.server = server.rstrip("/")
        self.topic = topic
        self.url = f"{self.server}/{self.topic}"
        
    def notify(
        self,
        title: str,
        message: str,
        action_url: str = None,
        priority: Union[int, str] = "default",
        tags: list = None
    ) -> bool:
        headers = {
            "Title": title,
            # Ntfy expects priority as a string (e.g. "default", "high") or int-as-string
            "Priority": str(priority)
        }
        if tags:
            headers["Tags"] = ",".join(tags)
            
        if action_url:
            headers["Click"] = action_url
            
        try:
            response = httpx.post(
                self.url,
                data=message.encode("utf-8"),
                headers=headers,
                timeout=5.0
            )
            response.raise_for_status()
            logger.info(f"Notifica inviata con successo al topic '{self.topic}'")
            return True
        except Exception as e:
            logger.error(f"Errore invio notifica: {e}")
            return False
