# SecureAccess Chain — Blockchain-based Identity & Access Management

A production-grade **Identity and Access Management (IAM)** system that
anchors every identity event on a tamper-proof blockchain ledger.

## Architecture

| Service | Stack | Port | Data store |
|---|---|---|---|
| **identity_service** | Django 5 + DRF + SimpleJWT | 8000 | PostgreSQL 16 |
| **ledger_service** | Flask 3 + PyMongo | 5001 | MongoDB 7 |
| **frontend** | Vanilla HTML / CSS / JS | 5500 (Live Server) | — |

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│   Frontend   │──────▶│ identity_service  │──────▶│ledger_service│
│  (browser)   │  JWT  │  Django + DRF     │ HTTP  │  Flask + Mongo│
└──────────────┘       └──────────────────┘       └──────────────┘
                              │                          │
                              ▼                          ▼
                         PostgreSQL                  MongoDB
```

## Quick start

### Prerequisites
- Docker & Docker Compose **or**
- Python 3.12+, PostgreSQL 16, MongoDB 7

### Using Docker Compose (recommended)

```bash
docker compose up --build
```

Services start on:
- Identity API → http://localhost:8000
- Ledger API → http://localhost:5001
- Open `frontend/index.html` with Live Server on port 5500

### Manual setup

```bash
# 1. Ledger service
cd ledger_service
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python app.py                     # starts on :5001

# 2. Identity service
cd identity_service
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver        # starts on :8000

# 3. Frontend
# Open frontend/index.html with VS Code Live Server
```

## Key features

| Feature | Description |
|---|---|
| **Decentralised Identities** | Every user gets a UUID-based DID on registration |
| **JWT Authentication** | Access + Refresh tokens via SimpleJWT |
| **RBAC + ABAC Policies** | Role-based *and* attribute-based access control |
| **Blockchain Audit Trail** | Every IAM event is hashed, chained, and stored in MongoDB |
| **Chain Verification** | One-click integrity check of the entire ledger |
| **Device Binding** | Bind physical devices to identities |
| **Session Management** | Track active sessions with IP and user-agent |

## API overview

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register/` | Register a new identity |
| POST | `/api/auth/login/` | Log in, receive JWT tokens |
| POST | `/api/auth/logout/` | Log out, end session |
| POST | `/api/auth/token/refresh/` | Refresh access token |

### Identities
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/identities/` | List identities (admin) |
| GET | `/api/identities/{id}/` | Retrieve identity |
| PATCH | `/api/identities/{id}/` | Update identity |
| DELETE | `/api/identities/{id}/` | Deactivate identity |

### Policies & Access
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/policies/` | List / create policies |
| GET/POST | `/api/access/grants/` | List / create access grants |
| POST | `/api/access/check/` | Evaluate access (policy engine) |

### Audit
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/audit/logs/` | Paginated blockchain blocks |
| GET | `/api/audit/verify/` | Verify chain integrity |

### Ledger (internal)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/blocks` | Ingest new block (API-key gated) |
| GET | `/blocks` | List blocks |
| GET | `/blocks/verify` | Verify chain |

## Project structure

```
secureaccess-chain/
├── identity_service/          # Django control plane
│   ├── config/                # settings, urls, wsgi, asgi
│   └── core/                  # models, views, serializers, services, tests
├── ledger_service/            # Flask blockchain ledger
│   ├── blockchain/            # block, chain, consensus
│   ├── routes/                # REST endpoints
│   └── db/                    # MongoDB client
├── frontend/                  # Vanilla HTML/CSS/JS dashboard
│   ├── css/
│   └── js/
├── docs/                      # Architecture, API spec
├── docker-compose.yml
└── README.md
```

## Environment variables

See `identity_service/.env` and `ledger_service/.env` for all
configurable values.

## License

This project is for academic / demonstration purposes.
