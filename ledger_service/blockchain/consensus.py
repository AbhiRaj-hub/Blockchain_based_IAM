"""
Proof of Authority with Ed25519 signatures.

Blocks are signed by a validator node. Verification needs only PUBLIC keys,
so auditors/other nodes can check the chain without being able to forge it.
This node holds one private key (VALIDATOR_PRIVATE_KEY); other validators'
public keys come from EXTRA_VALIDATOR_PUBLIC_KEYS.
"""

import base64
import binascii

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from config import EXTRA_VALIDATOR_PUBLIC_KEYS, THIS_VALIDATOR_ID, VALIDATOR_PRIVATE_KEY


class UnauthorizedValidatorError(Exception):
    pass


def _load_private_key(b64_seed: str) -> Ed25519PrivateKey:
    try:
        seed = base64.b64decode(b64_seed, validate=True)
        return Ed25519PrivateKey.from_private_bytes(seed)
    except (binascii.Error, ValueError) as exc:
        raise RuntimeError("VALIDATOR_PRIVATE_KEY must be base64 of exactly 32 random bytes.") from exc


_private_key = _load_private_key(VALIDATOR_PRIVATE_KEY)

_public_keys = {THIS_VALIDATOR_ID: _private_key.public_key()}
for _vid, _b64 in EXTRA_VALIDATOR_PUBLIC_KEYS.items():
    _public_keys[_vid] = Ed25519PublicKey.from_public_bytes(base64.b64decode(_b64, validate=True))


def sign_block(block_hash: str, validator_id: str) -> str:
    if validator_id != THIS_VALIDATOR_ID:
        raise UnauthorizedValidatorError(f"This node cannot sign as '{validator_id}'")
    return base64.b64encode(_private_key.sign(block_hash.encode())).decode()


def verify_signature(block_hash: str, validator_id: str, signature: str) -> bool:
    public_key = _public_keys.get(validator_id)
    if public_key is None or not signature:
        return False
    try:
        public_key.verify(base64.b64decode(signature, validate=True), block_hash.encode())
        return True
    except (InvalidSignature, binascii.Error, ValueError):
        return False
