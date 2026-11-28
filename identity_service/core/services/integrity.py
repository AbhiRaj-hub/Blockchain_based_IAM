from core.models import LedgerAnchor, PendingAnchor
from core.services.ledger_client import fetch_verify, lookup_missing

CHUNK = 500


def chain_status() -> dict:
    """
    Two independent checks:
      1. the ledger verifies its own hashes, links and signatures;
      2. every block hash this database recorded at write time must still exist on the chain
         (catches deleted/replaced blocks that a self-consistent chain cannot detect on its own).
    Raises LedgerError if the ledger is unreachable.
    """
    result = fetch_verify()
    hashes = list(LedgerAnchor.objects.values_list("block_hash", flat=True).distinct())
    missing = []
    for i in range(0, len(hashes), CHUNK):
        missing += lookup_missing(hashes[i : i + CHUNK])
    result["anchors_checked"] = len(hashes)
    result["anchors_missing"] = len(missing)
    if missing and result.get("valid"):
        result.update(valid=False, reason="anchor_missing")
    result["pending_anchors"] = PendingAnchor.objects.count()
    return result
