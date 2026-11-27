"""
A single ledger block. Deliberately simple and inspectable - the
security property this buys you is that changing any field changes
`hash`, and `hash` is what the next block links to, so tampering
with block N breaks every block after it.
"""

import hashlib
import json
from dataclasses import dataclass, field, fields, asdict
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_payload(payload: dict) -> str:
    """Deterministic hash of the event payload (sorted keys -> stable JSON)."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


@dataclass
class Block:
    index: int
    timestamp: str
    event_type: str
    payload: dict
    previous_hash: str
    validator_id: str = ""
    signature: str = ""
    hash: str = field(default="")

    def compute_hash(self) -> str:
        header = {
            "index": self.index,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "payload_hash": hash_payload(self.payload),
            "previous_hash": self.previous_hash,
            "validator_id": self.validator_id,
        }
        encoded = json.dumps(header, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    def finalize(self):
        """Call after validator_id/signature are set, before persisting."""
        self.hash = self.compute_hash()
        return self

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Block":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})

    @classmethod
    def genesis(cls) -> "Block":
        block = cls(
            index=0,
            timestamp=_now_iso(),
            event_type="genesis",
            payload={"message": "SecureAccess Chain genesis block"},
            previous_hash="0" * 64,
            validator_id="genesis",
        )
        return block.finalize()

    @classmethod
    def new(cls, index: int, event_type: str, payload: dict, previous_hash: str) -> "Block":
        return cls(
            index=index,
            timestamp=_now_iso(),
            event_type=event_type,
            payload=payload,
            previous_hash=previous_hash,
        )
