# small-cmr-password — Gestionale password (vault)

Vault password completo con cifratura AES-256-GCM, condivisione per utente/team/ditta e audit log su ogni evento di cambio password utente.

Il servizio espone due funzionalità distinte:
1. **Vault personale** (`/api/passwords/*`) — gestione credenziali utente con cifratura, reveal con re-auth, sharing
2. **Cambio password account** (`/api/users/me`) — modifica della propria password account con audit (bcrypt + verifica)

## Funzionalità vault

| Capability | Implementazione |
|------------|-----------------|
| Cifratura | AES-256-GCM con nonce univoco per record, chiave master 256-bit da `VAULT_MASTER_KEY` |
| Reveal | Richiede re-autenticazione con la propria password account |
| Sharing per utente | Permessi `read`/`write` individuali |
| Sharing per team | Espande automaticamente ai membri attivi del team |
| Sharing per ditta | Espande a tutti gli utenti della ditta |
| Filtri | Servizio, account_username, descrizione, owner_email (admin), include_shared |

## Porte

| Servizio | Porta |
|----------|-------|
| Backend  | 8004  |
| Frontend (preview) | 5176 |

Il frontend è esposto via Module Federation come modulo remote `password_module/PasswordsView`. L'app shell (`small-cmr-base` su porta 5173) lo carica nella route `/vault` con voce "Vault > Password" nella sidebar.

## Setup iniziale

**Prima di avviare è obbligatorio creare il file `.env`:**

```bash
cd backend
cp .env.example .env
```

Variabili da personalizzare in `backend/.env`:

| Variabile | Descrizione |
|-----------|-------------|
| `DATABASE_URL` | Stringa di connessione MySQL (porta 3307 in locale) |
| `SECRET_KEY` | Chiave JWT — deve essere uguale in tutti i servizi |
| `VAULT_MASTER_KEY` | Chiave master AES-256 (base64). Generare con: `python -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"` |

**ATTENZIONE**: cambiando `VAULT_MASTER_KEY` le password salvate non saranno più decifrabili.

## Avvio locale

```bash
# Backend
cd backend
python -m uvicorn main:app --reload --port 8004

# Frontend (modulo remote)
cd frontend
npm install
npm run build && npm run preview   # porta 5176
```

## API Routes

### Vault password

| Metodo | Path | Auth | Descrizione |
|--------|------|------|-------------|
| GET | `/api/passwords` | JWT | Lista con filtri (account_username, service, description, owner_email, include_shared) |
| GET | `/api/passwords/{id}` | JWT | Dettaglio (no password in chiaro) |
| POST | `/api/passwords/{id}/reveal` | JWT + password account | Restituisce password in chiaro |
| POST | `/api/passwords` | JWT | Crea record (password cifrata server-side) |
| PUT | `/api/passwords/{id}` | JWT (owner o write) | Aggiorna |
| DELETE | `/api/passwords/{id}` | JWT (owner o write) | Elimina |
| GET | `/api/passwords/{id}/shares` | JWT (owner o write) | Lista condivisioni |
| POST | `/api/passwords/{id}/shares` | JWT (owner o write) | Aggiungi/aggiorna condivisioni per utenti |
| POST | `/api/passwords/{id}/shares/team/{team_id}` | JWT | Condivide con tutti i membri di un team |
| POST | `/api/passwords/{id}/shares/ditta/{ditta_id}` | JWT | Condivide con tutti gli utenti di una ditta |
| DELETE | `/api/passwords/{id}/shares/{recipient_id}` | JWT | Revoca condivisione |

### Cambio password account

| Metodo | Path | Auth | Descrizione |
|--------|------|------|-------------|
| PUT | `/api/users/me` | JWT | Cambia password (richiede `password_attuale`) e/o nome/cognome |

## Modello dati

```
passwords
  id, account_username, encrypted_password (base64 AES-GCM),
  service, description, url, owner_id (FK users),
  created_at, updated_at

password_shares
  id, password_id (FK), recipient_id (FK users), shared_by_id (FK users),
  permission (read|write), created_at
  UNIQUE(password_id, recipient_id)
```

I team (`teams`, `team_members`) sono gestiti da `small-cmr-base` ma replicati come read-only in questo servizio per il `share_with_team`.

## Audit log

Tutti gli eventi di cambio password account (`PUT /api/users/me`) vengono scritti in `logs/audit.log` con timestamp, IP, user-agent, success/failure. Esempio:

```json
{
  "ts": "2026-06-07T22:35:12.412Z",
  "category": "audit",
  "event": "password_change",
  "action": "self_change",
  "actor_id": 42,
  "actor_email": "mario.rossi@esempio.com",
  "success": true,
  "ip": "10.0.0.1"
}
```

In produzione i log vengono inoltrati a Loki via Promtail.

## Test

```bash
cd backend
pytest tests/ -v
```

## Migrazioni DB

```bash
cd backend
alembic upgrade head
```

Migrations gestite:
- `001_initial.py` — no-op (users gestita da base)
- `002_vault.py` — tabelle `passwords` e `password_shares`
