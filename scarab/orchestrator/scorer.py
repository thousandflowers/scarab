import httpx
from typing import List, Optional
import logging
from scarab.config import global_config

logger = logging.getLogger(__name__)

class NodeScorer:
    def __init__(self, node_urls: List[str] = None):
        if not node_urls:
            self.node_urls = [global_config.get_primary_node_url()]
        else:
            self.node_urls = node_urls
        
    def get_best_node(self) -> Optional[str]:
        best_node = None
        best_score = -1.0
        
        for url in self.node_urls:
            try:
                resp = httpx.get(f"{url.rstrip('/')}/api/status", timeout=2.0)
                if resp.status_code == 200:
                    data = resp.json()
                    free_mb = data.get("disk_free_mb", 0)
                    cpu = data.get("cpu_usage_percent", 100)
                    
                    if free_mb < 500:
                        logger.warning(f"Nodo {url} ha disco quasi pieno (<500MB).")
                        continue
                        
                    score = free_mb - (cpu * 10)
                    if score > best_score:
                        best_score = score
                        best_node = url
            except Exception as e:
                logger.debug(f"Nodo {url} non raggiungibile. ({e})")
                
        return best_node
