import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from sqlite3.dbapi2 import Timestamp


def _now_iso()->str:
    return datetime.now(timezone.utc).isoformat()


def hash_payload(payload: dict)->str:
    "Hashing of the event"
    encoded = json.dumps(payload, sort_keys=True, separators=(",",":")).encode()
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


def compute_hash(self)->str:
    header = {
        "index": self.index,
        "timestamp": self.timestamp,
        "event_type": self.event_type,
        "payload_hash": hash_payload(self.payload),
        "previous_hash": self.previous_hash,
        "validator_id": self.validator_id
    }
    encoded = json.dumps(header, sort_keys=True, separators=(",",":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def finalize(self):
    "Call after signature"
    self.hash = self.compute_hash()
    return self


def to_dict(self)->dict:
    return asdict(self)


@classmethod
def from_dict(cls, data: dict)->"Block":
    data = {k: v for k, v in data.items() if k!="_id"}
    return cls(**data)


@classmethod
def genesis(cls)->"Block":
    block = cls(
        index=0,
        timestamp= _now_iso(),
        event_type= "genesis",
        payload= {"message":"Chain genesis Block"},
        previous_hash= "0"*64,
        validator_id= "genesis"
    )
    return block.finalize()


@classmethod
def new(cls, index: int, event_type: str, payload: dict, previous_hash: str)->"Block":
    return cls(
        index= index,
        timestamp= _now_iso(),
        event_type= event_type,
        payload= payload,
        previous_hash= previous_hash
    )
