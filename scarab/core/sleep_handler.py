import asyncio
import logging
from scarab.core.proxy_manager import disable_system_proxy, enable_system_proxy
from scarab.config import global_config

logger = logging.getLogger(__name__)

async def sleep_detector():
    """
    Rileva sleep e wake event da macOS per deregistrare 
    temporaneamente il proxy ed evitare blocchi di rete.
    Funziona guardando i salti temporali del loop asyncio,
    tecnica universale e a basso impatto CPU.
    """
    logger.info("Avvio Sleep Detector per macOS...")
    
    last_tick = asyncio.get_event_loop().time()
    while True:
        await asyncio.sleep(2)
        current_tick = asyncio.get_event_loop().time()
        
        # Se c'è un gap > 10s rispetto al ciclo atteso, il sistema
        # è andato in ibernazione e si è appena svegliato.
        if (current_tick - last_tick) > 10.0:
            logger.warning("Rilevato Wake-Up del sistema! Forzo la ri-registrazione del proxy.")
            disable_system_proxy()
            await asyncio.sleep(1)
            enable_system_proxy(global_config.get_proxy_port())
            
        last_tick = current_tick
