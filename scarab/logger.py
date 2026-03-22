import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    log_dir = "/var/log/scarab"
    # Fallback to local user dir if not root
    if os.geteuid() != 0:
        log_dir = os.path.expanduser("~/.scarab/logs")
        
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "scarab.log")
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Rimuovi eventuali handler esistenti
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logging.info(f"Logging inizializzato. File log rotativo in {log_file}")
