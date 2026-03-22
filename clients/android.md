# Installazione su Android

A causa delle severe policy di sicurezza e sandbox di Android, le intercettazioni tramite proxy TLS automatico sono più manuali rispetto ad iOS/macOS.

## Passaggi
1. Copia il file `certs/output/scarab-ca.pem`.
2. Vai in **Impostazioni > Sicurezza > Installazione certificato**.
3. Selezionalo e identificalo come "Certificato CA" (potresti dover usare un pin).
4. Vai in **Impostazioni > Reti Wi-Fi > Modifica Rete**.
5. Seleziona proxy manuale e inserisci `127.0.0.1` e porta `8080` (o l'IP di Tailscale se esposto remotamente sulla porta designata).
