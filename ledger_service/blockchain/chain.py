from pymongo.errors import DuplicateKeyError

from blockchain.block import Block
from blockchain.consensus import sign_block, verify_signature
from config import MAX_APPEND_RETRIES, THIS_VALIDATOR_ID
from db.mongo_client import get_blocks_collection

GENESIS_PREVIOUS = "0" * 64


class ChainConflictError(Exception):
    """Could not append because other writers kept winning the race."""


def get_latest_block() -> Block:
    collection = get_blocks_collection()
    doc = collection.find_one(sort=[("index", -1)])
    if doc is None:
        genesis = Block.genesis()
        try:
            collection.insert_one(genesis.to_dict())
            return genesis
        except DuplicateKeyError:  # another worker created it first
            doc = collection.find_one(sort=[("index", -1)])
    return Block.from_dict(doc)


def append_block(event_type: str, payload: dict, validator_id: str = THIS_VALIDATOR_ID) -> Block:
    """
    The only write path onto the chain. Safe under concurrency: the unique index
    on `index` makes a lost race raise DuplicateKeyError, and we retry on the new tip.
    """
    collection = get_blocks_collection()
    for _ in range(MAX_APPEND_RETRIES):
        latest = get_latest_block()
        block = Block.new(
            index=latest.index + 1, event_type=event_type, payload=payload, previous_hash=latest.hash
        )
        block.validator_id = validator_id
        block.hash = block.compute_hash()
        block.signature = sign_block(block.hash, validator_id)
        try:
            collection.insert_one(block.to_dict())
            return block
        except DuplicateKeyError:
            continue
    raise ChainConflictError("Too much write contention; retry")


def get_block(index: int) -> Block | None:
    doc = get_blocks_collection().find_one({"index": index})
    return Block.from_dict(doc) if doc else None


def list_blocks(limit: int = 100, skip: int = 0) -> list[Block]:
    cursor = get_blocks_collection().find().sort("index", -1).skip(skip).limit(limit)
    return [Block.from_dict(doc) for doc in cursor]


def missing_hashes(hashes: list[str]) -> list[str]:
    """Which of these block hashes are NOT on the chain (used for DB<->ledger cross-checks)."""
    found = {d["hash"] for d in get_blocks_collection().find({"hash": {"$in": hashes}}, {"hash": 1})}
    return [h for h in hashes if h not in found]


def validate_chain() -> dict:
    """
    Streams the whole chain in order and checks: contiguous indexes, a proper genesis,
    every hash recomputes, every previous_hash link, and an Ed25519 signature on every
    non-genesis block (the signature exemption applies to index 0 ONLY).
    """
    previous = None
    count = 0

    def fail(block_index, reason):
        return {"valid": False, "broken_at": block_index, "reason": reason, "length": count}

    for doc in get_blocks_collection().find().sort("index", 1):
        block = Block.from_dict(doc)
        count += 1
        expected_index = 0 if previous is None else previous.index + 1

        if block.index != expected_index:
            return fail(expected_index, "missing_block")
        if block.hash != block.compute_hash():
            return fail(block.index, "hash_mismatch")

        if block.index == 0:
            if block.event_type != "genesis" or block.previous_hash != GENESIS_PREVIOUS:
                return fail(0, "bad_genesis")
        else:
            if block.previous_hash != previous.hash:
                return fail(block.index, "broken_link")
            if not verify_signature(block.hash, block.validator_id, block.signature):
                return fail(block.index, "bad_signature")
        previous = block

    return {"valid": True, "broken_at": None, "reason": None, "length": count}
