import httpx
import logging
from scarab.orchestrator.scorer import NodeScorer
from scarab.core.local_handler import handle_local_offload

logger = logging.getLogger(__name__)

async def handle_offload(url: str, filename: str, headers: dict, size: int = None):
    scorer = NodeScorer()
    best_node = scorer.get_best_node()
    
    if best_node:
        logger.info(f"Nodo remoto trovato: {best_node}. Offloading '{filename}'...")
        try:
            payload = {
                "url": url,
                "filename": filename,
                "headers": headers
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{best_node.rstrip('/')}/api/jobs", json=payload, timeout=5.0)
                resp.raise_for_status()
                
            logger.info("Job accettato con successo dal nodo remoto.")
            return
        except Exception as e:
            logger.warning(f"Offload remoto fallito ({e}). Fallback locale in corso...")
    else:
        logger.warning("Nessun nodo remoto disponibile. Fallback locale in corso...")
        
    # Fallback locale
    await handle_local_offload(url, filename, headers, size)
