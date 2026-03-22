import logging
import subprocess
import os

logger = logging.getLogger(__name__)

def run_background():
    """Lancia Scarab come processo demone silenzioso."""
    logger.info("Avvio in background mode...")
    log_file = os.path.expanduser("~/.scarab/logs/scrb_bg.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, "a") as f:
        # Start cli-only mode bypassing mode selection to avoid loop
        # --local mode flag or an ENV variable could be safer
        env = os.environ.copy()
        env["SCARAB_FORCE_CLI"] = "1"
        subprocess.Popen(["scarab", "start"], stdout=f, stderr=f, start_new_session=True, env=env)
        
    logger.info(f"Processo detached avviato. Log: {log_file}")
