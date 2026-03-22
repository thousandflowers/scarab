# Contribuire a Scarab

1. **Test reale**: Tutte le feature devono funzionare su hardware reale (Mac, Pi).
2. **Setup dell'ambiente**: Usa il virtual environment della directory `scarab` (Python 3.11+).
3. **Formattazione**: Usa `black` e `ruff` prima di fare commit. `pytest` per i test inclusi in `tests/`.
4. **Stabilità di Rete**: Tutto quello che interagisce con il proxy di sistema deve prevedere segnali SIGINT/SIGTERM e de-registrare il proxy in caso di fallimento o chiusura.
