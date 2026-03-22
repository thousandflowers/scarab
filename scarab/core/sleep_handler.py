import asyncio
import subprocess
import logging
from scarab.cli import disable_system_proxy, enable_system_proxy
from scarab.config import global_config

logger = logging.getLogger(__name__)

async def sleep_detector():
    """
    Rileva sleep e wake event da macOS per deregistrare 
    temporaneamente il proxy ed evitare blocchi di rete.
    """
    logger.info("Avvio Sleep Detector per macOS...")
    
    # Esegue `pmset -g log` o simili o usiamo un workaround guardando i salti temporali
    # che è molto più universale e meno CPU intensive.
    
    last_tick = asyncio.get_event_loop().time()
    while True:
        await asyncio.sleep(2)
        current_tick = asyncio.get_event_loop().time()
        
        # Se c'è un gap temporale di > 10 secondi rispetto al ciclo sleep atteso,
        # significa che il computer è andato in ibernazione ed è ora sveglio.
        if (current_tick - last_tick) > 10.0:
            logger.warning("Rilevato Wake-Up del sistema! Forzo la ri-registrazione del proxy.")
            disable_system_proxy()
            await asyncio.sleep(1)
            enable_system_proxy(global_config.get_proxy_port())
            
        last_tick = current_tick
