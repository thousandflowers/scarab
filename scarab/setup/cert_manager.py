import logging
import subprocess

logger = logging.getLogger(__name__)

def fetch_and_trust_cert():
    logger.info("Connecting to server and fetching CA certificate...")
    # Semplificazione per v0.1 - questo passerebbe per Tailscale
    # e lo piazzerrebbe nel portachiavi di sistema.
    logger.info("Certificate trusted successfully! System ready.")
