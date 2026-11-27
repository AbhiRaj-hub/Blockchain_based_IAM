import os

from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable {name}. "
            "Run `python scripts/generate_env.py` (see docs/SETUP.md)."
        )
    return value


def _parse_public_keys(raw: str) -> dict:
    """'node-2:BASE64KEY,node-3:BASE64KEY' -> {'node-2': 'BASE64KEY', ...}"""
    keys = {}
    for item in filter(None, (p.strip() for p in raw.split(","))):
        vid, _, key = item.partition(":")
        if not vid or not key:
            raise RuntimeError("EXTRA_VALIDATOR_PUBLIC_KEYS must look like 'node-2:BASE64,node-3:BASE64'")
        keys[vid] = key
    return keys


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "secureaccess_ledger")

# Identity of THIS node and its Ed25519 private key (base64 of a 32-byte seed).
THIS_VALIDATOR_ID = os.getenv("VALIDATOR_ID", "node-1")
VALIDATOR_PRIVATE_KEY = _required("VALIDATOR_PRIVATE_KEY")

# Public keys of any OTHER validators whose blocks this node should accept.
EXTRA_VALIDATOR_PUBLIC_KEYS = _parse_public_keys(os.getenv("EXTRA_VALIDATOR_PUBLIC_KEYS", ""))

# Shared bearer token the Django control plane must send on EVERY ledger call.
INGEST_API_KEY = _required("INGEST_API_KEY")
if len(INGEST_API_KEY) < 24:
    raise RuntimeError("INGEST_API_KEY must be at least 24 characters long.")

MAX_APPEND_RETRIES = int(os.getenv("MAX_APPEND_RETRIES", "8"))
