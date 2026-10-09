# API Specification — SecureAccess Chain

## Overview
This document specifies the REST endpoints for both the `identity_service` (port 8000) and `ledger_service` (port 5001).

---

## 1. Identity Service (`http://localhost:8000`)

### Authentication

#### `POST /api/auth/register/`
Register a new digital identity.
- **Access**: Public
- **Request Body**:
  ```json
  {
    "username": "alice",
    "email": "alice@example.com",
    "password": "SecurePassword123!",
    "password_confirm": "SecurePassword123!",
    "role": "user"
  }
  ```
- **Response** (`201 Created`):
  ```json
  {
    "id": 1,
    "did": "4c9d7249-16a3-41bb-b097-f58c7e19d7b8",
    "username": "alice",
    "email": "alice@example.com",
    "role": "user",
    "is_active": true,
    "date_joined": "2026-10-08T14:30:00Z"
  }
  ```

#### `POST /api/auth/login/`
Authenticate user, start an active session, and receive JWT tokens.
- **Access**: Public
- **Request Body**:
  ```json
  {
    "username": "alice",
    "password": "SecurePassword123!"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "access": "eyJhbGciOiJIUzI1Ni...",
    "refresh": "eyJhbGciOiJIUzI1Ni...",
    "user": {
      "id": 1,
      "username": "alice",
      "did": "4c9d7249-16a3-41bb-b097-f58c7e19d7b8",
      "role": "user"
    }
  }
  ```

#### `POST /api/auth/logout/`
Deactivates active session and records an `identity_logout` blockchain block.
- **Access**: Authenticated (`Bearer <token>`)
- **Response** (`200 OK`):
  ```json
  {
    "message": "Logged out successfully"
  }
  ```

#### `POST /api/auth/token/refresh/`
Refresh expired JWT access token.
- **Access**: Public
- **Request Body**: `{"refresh": "<refresh_token>"}`
- **Response** (`200 OK`): `{"access": "<new_access_token>"}`

---

### Identity Management

#### `GET /api/identities/`
List identities.
- **Access**: Admin or Auditor

#### `GET /api/identities/{id}/`
Retrieve details of a single identity.
- **Access**: Admin or Owner

#### `PATCH /api/identities/{id}/`
Update identity metadata, public keys, or role.
- **Access**: Admin or Owner

---

### Access Control & Policy Engine

#### `GET /api/policies/` & `POST /api/policies/`
Manage access policies.
- **Access**: Admin
- **Policy Schema**:
  ```json
  {
    "name": "Finance-DB-Read",
    "description": "Allow read operations on financial ledger database",
    "resource": "database:finance",
    "action": "read",
    "effect": "allow",
    "conditions": {
      "roles": ["auditor", "admin"],
      "allowed_hours": [9, 17]
    },
    "priority": 10,
    "is_active": true
  }
  ```

#### `GET /api/access/grants/` & `POST /api/access/grants/`
Issue or revoke access grants tying an `Identity` to a `Policy`.
- **Access**: Admin (create), Authenticated (read self)

#### `POST /api/access/check/`
Evaluate RBAC + ABAC policy engine for access decisions.
- **Access**: Authenticated
- **Request Body**:
  ```json
  {
    "identity_id": 1,
    "resource": "database:finance",
    "action": "read"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "allowed": true,
    "matched_policies": ["Finance-DB-Read"],
    "reason": "Access granted by policy Finance-DB-Read"
  }
  ```

---

### Blockchain & Audit (Proxied to Ledger Service)

#### `GET /api/audit/logs/?page=1&page_size=20`
Fetch paginated blockchain blocks.
- **Access**: Admin or Auditor

#### `GET /api/audit/verify/`
Verify cryptographic integrity and linkage of the blockchain ledger.
- **Access**: Admin or Auditor
- **Response** (`200 OK`):
  ```json
  {
    "valid": true,
    "block_count": 42,
    "errors": []
  }
  ```

---

## 2. Ledger Microservice (`http://localhost:5001`)

Protected by `X-Api-Key` header (`LEDGER_INGEST_API_KEY`).

#### `POST /blocks`
Ingests a new state block into the chain.
- **Headers**: `X-Api-Key: <api_key>`
- **Request Body**:
  ```json
  {
    "event_type": "identity_registered",
    "payload": { "username": "alice", "did": "..." },
    "validator_id": "identity_service"
  }
  ```
- **Response** (`201 Created`): Returns complete finalized block with SHA-256 hash.

#### `GET /blocks`
Query blocks ordered by block index ascending or descending with pagination.

#### `GET /blocks/{index}`
Retrieve single block by index.

#### `GET /blocks/verify`
Full chain traversal verifying hash continuity and payload integrity.
