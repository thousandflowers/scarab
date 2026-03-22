import httpx
import logging
import time
import asyncio
from scarab.orchestrator.scorer import NodeScorer
from scarab.core.local_handler import handle_local_offload

logger = logging.getLogger(__name__)

async def handle_offload(url: str, filename: str, headers: dict, size: int = None):
    scorer = NodeScorer()
    best_node = scorer.get_best_node()
    
    if best_node:
        logger.info(f"Nodo remoto trovato: {best_node}. Offloading '{filename}'...")
        start_time = time.time()
        success = False
        
        while time.time() - start_time < 30.0:
            try:
                payload = {
                    "url": url,
                    "filename": filename,
                    "headers": headers
                }
                async with httpx.AsyncClient() as client:
                    resp = await client.post(f"{best_node.rstrip('/')}/api/jobs", json=payload, timeout=5.0)
                    resp.raise_for_status()
                success = True
                break
            except httpx.RequestError:
                logger.warning(f"Nodo {best_node} irraggiungibile. Ritento tra 5s...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.warning(f"Offload remoto API error ({e}). Nuovo tentativo in 5s...")
                await asyncio.sleep(5)
                
        if success:
            logger.info("Job accettato con successo dal nodo remoto.")
            return
        else:
            logger.warning("Timeout 30s superato o nodo irraggiungibile. Fallback locale in corso...")
    else:
        logger.warning("Nessun nodo remoto disponibile. Fallback locale in corso...")
        
    # Fallback locale
    await handle_local_offload(url, filename, headers, size)
