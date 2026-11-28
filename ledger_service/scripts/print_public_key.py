#!/usr/bin/env python3
"""Print this node's Ed25519 PUBLIC key (safe to share). Needed when adding this node to another node's
EXTRA_VALIDATOR_PUBLIC_KEYS, or when keeping an old key trusted after rotation.

    VALIDATOR_PRIVATE_KEY=... python scripts/print_public_key.py
    docker compose exec ledger_service python scripts/print_public_key.py
"""
import base64
import os
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

seed = os.getenv("VALIDATOR_PRIVATE_KEY")
if not seed:
    sys.exit("VALIDATOR_PRIVATE_KEY is not set")
public = Ed25519PrivateKey.from_private_bytes(base64.b64decode(seed)).public_key().public_bytes(
    serialization.Encoding.Raw, serialization.PublicFormat.Raw)
print(f"{os.getenv('VALIDATOR_ID', 'node-1')}:{base64.b64encode(public).decode()}")
