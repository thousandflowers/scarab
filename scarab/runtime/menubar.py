import logging
import subprocess

logger = logging.getLogger(__name__)

def run_menubar():
    """Lancia l'app menubar MacOS (richiede 'rumps')."""
    try:
        import rumps
    except ImportError:
        logger.error("rumps library is required for menubar mode on macOS.")
        return

    class ScarabApp(rumps.App):
        def __init__(self):
            super(ScarabApp, self).__init__("Scarab")

        @rumps.clicked("Toggle Proxy")
        def onoff(self, _):
            rumps.notification("Scarab", "Proxy Config", "Toggle features are CLI-driven in v0.1.")

        @rumps.clicked("Open FileBrowser")
        def open_fb(self, _):
            subprocess.run(["scarab", "mount"], check=False)

    logger.info("Avviando l'app Menu Bar. L'icona Scarab apparirà in alto a destra.")
    ScarabApp().run()
