import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

def _get_headers()->dict:
    return {"X-Api-Key": settings.LEDGER_INGEST_API_KEY}

def post_event(event_type: str, payload: dict, validator_id: str = "identity_service")->dict:
    url = f"{settings.LEDGER_SERVICE_URL}/blocks"
    data = {
        "event_type": event_type,
        "payload": payload,
        "validator_id": validator_id
    }
    logger.info(f"Posting event {event_type} to ledger")
    resp = requests.post(url, json=data, headers=_get_headers(), timeout=5)
    resp.raise_for_status()
    return resp.json()

def get_blocks(page: int = 1, page_size: int = 20)->dict:
    url = f"{settings.LEDGER_SERVICE_URL}/blocks"
    params = {"page": page, "size": page_size}
    resp = requests.get(url, params=params, headers=_get_headers(), timeout=5)
    resp.raise_for_status()
    return resp.json()

def verify_chain()->dict:
    url = f"{settings.LEDGER_SERVICE_URL}/blocks/verify"
    resp = requests.get(url, headers=_get_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()

def get_block(index: int)->dict:
    url = f"{settings.LEDGER_SERVICE_URL}/blocks/{index}"
    resp = requests.get(url, headers=_get_headers(), timeout=5)
    resp.raise_for_status()
    return resp.json()
