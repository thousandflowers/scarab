# Installazione su macOS

Scarab richiede l'installazione del certificato generato per poter intercettare il traffico TLS senza far scattare avvisi di sicurezza sul browser.

## Passaggi
1. Avvia Scarab sul Mac (`scarab start`)
2. Esegui il comando di auto-installazione:
   `sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain certs/output/scarab-ca.pem`
3. Chiudi e riapri il browser.
