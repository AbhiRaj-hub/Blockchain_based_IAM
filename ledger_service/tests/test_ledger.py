import base64
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("INGEST_API_KEY", "test-ingest-key-test-ingest-key-123")
os.environ.setdefault("VALIDATOR_PRIVATE_KEY", base64.b64encode(os.urandom(32)).decode())

import mongomock  # noqa: E402

from blockchain.block import Block  # noqa: E402
from blockchain.consensus import UnauthorizedValidatorError, sign_block, verify_signature  # noqa: E402

KEY = os.environ["INGEST_API_KEY"]
AUTH = {"Authorization": f"Bearer {KEY}"}


class BlockAndConsensusTests(unittest.TestCase):
    def test_changing_payload_changes_hash(self):
        block = Block.new(1, "identity_created", {"role": "employee"}, "0" * 64)
        block.validator_id = "node-1"
        block.finalize()
        original = block.hash
        block.payload["role"] = "admin"
        self.assertNotEqual(block.compute_hash(), original)

    def test_signature_roundtrip(self):
        sig = sign_block("abc", "node-1")
        self.assertTrue(verify_signature("abc", "node-1", sig))
        self.assertFalse(verify_signature("abd", "node-1", sig))      # different message
        self.assertFalse(verify_signature("abc", "rogue", sig))       # unknown validator
        self.assertFalse(verify_signature("abc", "node-1", ""))       # missing signature
        self.assertFalse(verify_signature("abc", "node-1", "not base64!!"))

    def test_cannot_sign_as_another_validator(self):
        with self.assertRaises(UnauthorizedValidatorError):
            sign_block("abc", "node-2")

    def test_from_dict_ignores_unknown_fields(self):
        data = Block.genesis().to_dict() | {"_id": 1, "extra": {}}
        self.assertEqual(Block.from_dict(data).index, 0)


class ChainAndRouteTests(unittest.TestCase):
    def setUp(self):
        self.collection = mongomock.MongoClient().db.blocks
        self.collection.create_index("index", unique=True)
        self.collection.create_index("hash", unique=True)
        self.patches = [
            patch("blockchain.chain.get_blocks_collection", return_value=self.collection),
            patch("app.get_blocks_collection", return_value=self.collection),
        ]
        for p in self.patches:
            p.start()
        from app import create_app

        self.client = create_app().test_client()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def post(self, event="identity_created", payload=None):
        return self.client.post("/blocks", json={"event_type": event, "payload": payload or {"did": "d1"}}, headers=AUTH)

    def verify(self):
        return self.client.get("/blocks/verify", headers=AUTH)

    # ---- access control ----
    def test_every_endpoint_requires_the_api_key(self):
        for method, path in [("get", "/blocks"), ("post", "/blocks"), ("get", "/blocks/verify"),
                             ("get", "/blocks/0"), ("post", "/blocks/lookup")]:
            self.assertEqual(getattr(self.client, method)(path).status_code, 401, f"{method} {path}")
        self.assertEqual(self.client.get("/blocks", headers={"Authorization": "Bearer wrong"}).status_code, 401)

    def test_rejects_malformed_events(self):
        for body in ({}, {"event_type": "x"}, {"event_type": "x", "payload": "str"}, {"event_type": "", "payload": {}}):
            self.assertEqual(self.client.post("/blocks", json=body, headers=AUTH).status_code, 400)

    # ---- integrity ----
    def test_chain_links_and_verifies(self):
        a, b = self.post().get_json(), self.post("access_granted").get_json()
        self.assertEqual(b["previous_hash"], a["hash"])
        res = self.verify()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["length"], 3)  # genesis + 2

    def test_payload_tampering_detected(self):
        self.post(); self.post("access_granted")
        self.collection.update_one({"index": 1}, {"$set": {"payload": {"did": "attacker"}}})
        res = self.verify()
        self.assertEqual(res.status_code, 409)
        self.assertEqual((res.get_json()["broken_at"], res.get_json()["reason"]), (1, "hash_mismatch"))

    def test_forged_signature_detected(self):
        self.post()
        self.collection.update_one({"index": 1}, {"$set": {"signature": base64.b64encode(b"x" * 64).decode()}})
        self.assertEqual(self.verify().get_json()["reason"], "bad_signature")

    def test_attacker_recomputed_hash_still_fails_without_the_private_key(self):
        self.post()
        doc = self.collection.find_one({"index": 1})
        forged = Block.from_dict(doc)
        forged.payload = {"did": "attacker"}
        forged.hash = forged.compute_hash()  # attacker can recompute the hash...
        self.collection.update_one({"index": 1}, {"$set": {"payload": forged.payload, "hash": forged.hash}})
        self.assertEqual(self.verify().get_json()["reason"], "bad_signature")  # ...but not the signature

    def test_fake_genesis_typed_block_does_not_bypass_signature_check(self):
        self.post()
        tip = Block.from_dict(self.collection.find_one({"index": 1}))
        fake = Block.new(2, "genesis", {"evil": True}, tip.hash)
        fake.validator_id = "node-1"
        fake.finalize()  # valid hash, link and index, but unsigned
        self.collection.insert_one(fake.to_dict())
        self.assertEqual(self.verify().get_json()["reason"], "bad_signature")

    def test_deleted_block_detected(self):
        for _ in range(3):
            self.post()
        self.collection.delete_one({"index": 2})
        res = self.verify().get_json()
        self.assertEqual((res["valid"], res["reason"]), (False, "missing_block"))

    def test_altered_genesis_detected(self):
        self.post()
        self.collection.update_one({"index": 0}, {"$set": {"payload": {"message": "x"}}})
        self.assertEqual(self.verify().get_json()["reason"], "hash_mismatch")

    # ---- concurrency ----
    def test_append_retries_after_losing_a_race(self):
        self.post()  # tip is now block 1
        from blockchain import chain

        stale = Block.from_dict(self.collection.find_one({"index": 0}))
        real_tip = chain.get_latest_block
        with patch("blockchain.chain.get_latest_block", side_effect=[stale, real_tip()]):
            res = self.post("access_granted")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["index"], 2)
        self.assertTrue(self.verify().get_json()["valid"])

    # ---- cross-check helper ----
    def test_lookup_reports_hashes_missing_from_chain(self):
        good = self.post().get_json()["hash"]
        res = self.client.post("/blocks/lookup", json={"hashes": [good, "f" * 64]}, headers=AUTH)
        self.assertEqual(res.get_json()["missing"], ["f" * 64])

    def test_health(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
