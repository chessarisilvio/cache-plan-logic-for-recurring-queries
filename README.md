# Cache Plan Logic for Recurring Queries

## Descrizione
Questo progetto implementa una cache semantica per i piani di azione ricorrenti generati dal worker LLM locale. Lo scopo è evitare di rieseguire l'inferenza del modello 35B su query ripetute, riducendo latenza e carico sulla GPU Tesla P40.

## Architettura
- **Modulo cache** (`src/cache.py`): gestisce lo storage SQLite delle entry di piano.
- **Wrapper worker** (`src/worker.py`: stub che intercetta la fase di pianificazione e usa la cache.
- **Chiave di cache**: hash SHA-256 della query normalizzata più contesto (es. fascia oraria).
- **Valore di cache**: piano JSON serializzato prodotto dal LLM.
- **Politica di scadenza**: TTL basato sul tempo (default 24h) con invalidazione context-aware.

## Installazione
1. Clonare il repository.
2. Assicurarsi di avere Python 3.12+ e le dipendenze richieste (sqlite3 è nello standard library).
3. Facoltativamente creare un ambiente virtuale e installare eventuali pacchetti aggiuntivi specificati in `requirements.txt` (se presente).
4. Il modulo è progettato per essere importato dal worker principale del sistema AI locale.

## Uso
Il worker chiama `get_cached_plan(query, context)` prima di avviare l'inferenza. Se esiste una entry valida, restituisce il piano cached; altrimenti procede con l'inferenza e salva il risultato in cache tramite `store_plan(query, context, plan)`.

## Esempi
```python
from src.cache import get_cached_plan, store_plan

query = "controlla la posta"
context = {"hour_bucket": 123}
plan = get_cached_plan(query, context)
if plan is None:
    # Esegui inferenza LLM per ottenere il piano
    plan = generate_plan_with_llm(query, context)
    store_plan(query, context, plan)
# Esegui il piano
```

## Stato
✅ COMPLETATO — 2026-06-12
Tutte le fasi sono state realizzate:
- Definizione requisiti e design
- Implementazione modulo cache
- Integrazione stub nel worker
- Script/README per test manuale su GPU libera