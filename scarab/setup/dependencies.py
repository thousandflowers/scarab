import os
import shutil
import platform
import subprocess
import logging
import uuid
from scarab.config import global_config

logger = logging.getLogger(__name__)

SCARAB_BIN_DIR = os.path.expanduser("~/.scarab/bin")

def ensure_aria2c() -> str:
    """Verifica e installa aria2c se non presente. Ritorna il path."""
    if shutil.which("aria2c"):
        return shutil.which("aria2c")
        
    local_aria2c = os.path.join(SCARAB_BIN_DIR, "aria2c")
    if os.path.exists(local_aria2c) and os.access(local_aria2c, os.X_OK):
        return local_aria2c
        
    logger.info("aria2c non trovato. Risoluzione dipendenze in corso...")
    system = platform.system().lower()
    
    if system == "darwin":
        if shutil.which("brew"):
            logger.info("Uso Homebrew per installare aria2 su macOS...")
            subprocess.run(["brew", "install", "aria2"], check=True)
            return shutil.which("aria2c")
        else:
            raise RuntimeError("aria2c non trovato e Homebrew non installato. Impossibile risolvere la dipendenza su macOS.")
    else:
        logger.warning(f"Installazione automatica aria2c non gestita per {system}.")
        return ""

def ensure_ntfy_topic():
    """Genera topic ntfy random alla prima esecuzione se è quello di default"""
    topic = global_config.get_ntfy_topic()
    if topic == "scarab_alerts" or not topic:
        new_topic = f"scrb_{uuid.uuid4().hex[:12]}"
        logger.info(f"Generato nuovo topic ntfy sicuro: {new_topic}")
        global_config.update("notifier", "ntfy_topic", new_topic)

def ensure_all():
    try:
        ensure_aria2c()
    except Exception as e:
        logger.error(f"Errore dipendenze: {e}")
    ensure_ntfy_topic()
