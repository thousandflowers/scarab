import logging
from scarab.config import global_config

logger = logging.getLogger(__name__)

def set_mode(mode: str):
    logger.info(f"Impostazione Runtime Mode: {mode}")
    global_config.update("proxy", "runtime_mode", mode)
    logger.info(f"Al prossimo riavvio di 'scarab start', userà la modalità: {mode}")

def get_mode() -> str:
    return global_config.parser.get("proxy", "runtime_mode", fallback="menubar")
