import hmac
from .block import Block


def is_authorized_validator(api_key: str, expected_key: str)->bool:
    "Check if API key matches securely"
    if not api_key or not expected_key:
        return False
    return hmac.compare_digest(api_key.encode(), expected_key.encode())


def validate_block(block: Block, previous_block: Block)->tuple[bool, str]:
    "Validate a single block"
    if block.index != previous_block.index + 1:
        return False, "Index is not sequential"
    if block.previous_hash != previous_block.hash:
        return False, "Previous hash mismatch"
    if block.hash != block.compute_hash():
        return False, "Hash is invalid"
    return True, ""
