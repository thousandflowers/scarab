# Scarab

Un sistema che intercetta automaticamente i download pesanti dal Mac e li offloada su un Raspberry Pi per non rallentare l'accesso alla rete o consumare disco locale.

## Obiettivo (v0.1)
Scarab intercetta i download che superano una certa dimensione (es. 100MB), li blocca sul Mac, e delega il download a un Raspberry Pi nella tua rete (via Tailscale) che lo scarica su un disco esterno SSD. Quando il download è terminato, ricevi una notifica push e puoi accedere al file tramite FileBrowser.

## Principi di Sviluppo
- **Core first**: niente feature superflue.
- **Test reale**: fail se qualcosa va storto, nessuna rottura silenziosa.
- **Fail loudly**: il sistema proxy deve disinstallarsi in caso di crash per non rompere la rete.
