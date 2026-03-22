# Architettura Tecnica

- **Mitmproxy Addon**: Funziona come proxy di sistema su macOS per intercettare il traffico HTTP(s). Legge gli header `Content-Length` o `Content-Type` e se la condizione di offload è soddisfatta (es. file > 100MB), interrompe il flusso ed estrae i metadati (Cookie, User-Agent, ecc.).
- **Aria2**: Utilizzato come downloader demonizzato. Richiamato via JSON-RPC dall'orchestrator.
- **FastAPI / Orchestrator**: Esposto sul Pi per ricevere i job di offloading.
- **Ntfy**: Sistema per le notifiche push sui file scaricati.
- **Tailscale**: Per garantire l'accesso sicuro.

## Panoramica Componenti
- `scarab.proxy`: Mitmproxy addon e logica di ispezione HTTP.
- `scarab.orchestrator`: App FastAPI per ricevere i task di offload.
- `scarab.downloader`: Client RPC per Aria2.
- `scarab.notifier`: Client HTTP per Ntfy.
- `scarab.network`: Utility (Tailscale scanner, etc.).
- `scarab.scheduler`: Jobs periodici (pulitura, status checker).
