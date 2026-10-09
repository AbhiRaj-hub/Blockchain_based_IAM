# Architecture — SecureAccess Chain

## Overview

SecureAccess Chain is a **Blockchain-based Identity and Access Management**
(IAM) system built with a microservice architecture. Every significant
identity event (registration, login, access grant, policy change) is
recorded as a tamper-proof block on a hash-linked ledger.

## System diagram

```
                          ┌──────────────────────────────────┐
                          │            Frontend              │
                          │   (Vanilla HTML / CSS / JS)      │
                          │   Served via Live Server :5500   │
                          └───────────────┬──────────────────┘
                                          │ JWT-authenticated
                                          │ REST calls
                          ┌───────────────▼──────────────────┐
                          │        identity_service          │
                          │   Django 5 + DRF + SimpleJWT     │
                          │          Port 8000               │
                          │                                  │
                          │  ┌────────┐  ┌───────────────┐   │
                          │  │ Models │  │ Policy Engine │   │
                          │  └───┬────┘  │  RBAC + ABAC  │   │
                          │      │       └───────────────┘   │
                          │      ▼                           │
                          │  PostgreSQL 16                   │
                          │  (identities, policies, grants)  │
                          └───────────────┬──────────────────┘
                                          │  HTTP + API key
                          ┌───────────────▼──────────────────┐
                          │         ledger_service           │
                          │     Flask 3 + PyMongo            │
                          │          Port 5001               │
                          │                                  │
                          │  ┌────────────────────────────┐  │
                          │  │  Blockchain Engine         │  │
                          │  │  Block → Chain → Consensus │  │
                          │  └────────────┬───────────────┘  │
                          │               ▼                  │
                          │         MongoDB 7                │
                          │    (blocks collection)           │
                          └──────────────────────────────────┘
```

## Components

### 1. identity_service (Django)

| Module | Responsibility |
|---|---|
| `core/models.py` | Identity (custom User), DeviceBinding, LedgerAnchor, Policy, AccessGrant, Session |
| `core/views.py` | REST endpoints for auth, identities, devices, policies, grants, audit |
| `core/serializers.py` | DRF serializers for request/response validation |
| `core/permissions.py` | IsAdmin, IsAdminOrAuditor, IsOwnerOrAdmin |
| `core/services/policy_engine.py` | Evaluates RBAC + ABAC policies for access decisions |
| `core/services/ledger_client.py` | HTTP client that posts events to the ledger service |

**Authentication flow:**
1. User registers → Identity created in PostgreSQL → `identity_registered` event posted to ledger
2. User logs in → JWT tokens issued → Session record created → `identity_login` event posted
3. User logs out → Session deactivated → `identity_logout` event posted

**Access control flow:**
1. Admin creates a Policy (resource + action + effect + ABAC conditions)
2. Admin grants the Policy to an Identity via AccessGrant
3. On access check, the policy engine evaluates all active grants:
   - Filters by resource and action
   - Evaluates ABAC conditions (role, time, attributes)
   - Deny policies override allow policies

### 2. ledger_service (Flask)

| Module | Responsibility |
|---|---|
| `blockchain/block.py` | Block dataclass with SHA-256 hashing |
| `blockchain/chain.py` | Chain assembly: append, validate, initialize |
| `blockchain/consensus.py` | Proof-of-Authority validator verification |
| `routes/blocks.py` | REST endpoints: POST /blocks, GET /blocks, GET /blocks/verify |
| `db/mongo_client.py` | PyMongo connection and collection management |

**Block structure:**
```json
{
  "index": 1,
  "timestamp": "2024-01-15T10:30:00+00:00",
  "event_type": "identity_registered",
  "payload": { "username": "alice", "did": "..." },
  "previous_hash": "abc123...",
  "validator_id": "identity_service",
  "signature": "",
  "hash": "def456..."
}
```

**Chain validation** verifies:
- Every block's stored hash matches its recomputed hash
- Every block's `previous_hash` matches the prior block's `hash`
- Block indices are sequential (0, 1, 2, …)

### 3. Frontend

Vanilla HTML/CSS/JS dashboard with pages for:
- **Login / Register** — JWT-based auth
- **Dashboard** — Stats overview and recent activity
- **Identities** — CRUD for digital identities
- **Access Control** — Policy and access-grant management with live access check
- **Assets** — Resource catalogue
- **Audit** — Blockchain log viewer with chain verification

## Data flow — registering a new identity

```
1. User fills register form in frontend
2. Frontend POSTs to identity_service /api/auth/register/
3. identity_service creates Identity in PostgreSQL
4. identity_service calls ledger_client.post_event("identity_registered", {...})
5. ledger_client POSTs to ledger_service /blocks
6. ledger_service creates Block, appends to chain in MongoDB
7. ledger_service returns block dict
8. identity_service creates LedgerAnchor linking Identity ↔ Block
9. identity_service returns success to frontend
```

## Security considerations

- JWT tokens with 30-minute access / 1-day refresh lifetimes
- Ledger service protected by API key (X-Api-Key header)
- CORS restricted to allowed origins
- Passwords hashed with Django's PBKDF2 hasher
- Blockchain hashes use SHA-256
- ABAC conditions support time-of-day and role-based restrictions
