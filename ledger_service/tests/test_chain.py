import unittest
from blockchain.block import Block
from blockchain.chain import initialize_chain, append_block, validate_chain, get_latest_block


class MockCollection:
    def __init__(self):
        self.docs = []
        
    def find_one(self, filter=None, sort=None):
        if not self.docs:
            return None
        if sort and sort[0][0] == "index" and sort[0][1] == -1:
            return max(self.docs, key=lambda x: x["index"])
        return self.docs[0] if self.docs else None
        
    def find(self, sort=None):
        docs = list(self.docs)
        if sort and sort[0][0] == "index":
            docs.sort(key=lambda x: x["index"], reverse=(sort[0][1] == -1))
        return docs
        
    def insert_one(self, doc):
        self.docs.append(doc)
        
    def count_documents(self, filter):
        return len(self.docs)


class TestChain(unittest.TestCase):
    def setUp(self):
        self.collection = MockCollection()

    def test_initialize_chain(self):
        initialize_chain(self.collection)
        self.assertEqual(len(self.collection.docs), 1)
        self.assertEqual(self.collection.docs[0]["index"], 0)
        self.assertEqual(self.collection.docs[0]["event_type"], "genesis")

    def test_append_block(self):
        initialize_chain(self.collection)
        block = append_block(self.collection, "test", {"msg": "hi"}, "val1")
        
        self.assertEqual(block.index, 1)
        self.assertEqual(block.validator_id, "val1")
        self.assertEqual(len(self.collection.docs), 2)
        
        latest = get_latest_block(self.collection)
        self.assertEqual(latest.index, 1)
        self.assertEqual(latest.hash, block.hash)

    def test_validate_chain_valid(self):
        initialize_chain(self.collection)
        append_block(self.collection, "test1", {"msg": "hi1"}, "val1")
        append_block(self.collection, "test2", {"msg": "hi2"}, "val2")
        
        result = validate_chain(self.collection)
        self.assertTrue(result["valid"])
        self.assertEqual(result["block_count"], 3)
        self.assertEqual(len(result["errors"]), 0)

    def test_validate_chain_tampered(self):
        initialize_chain(self.collection)
        append_block(self.collection, "test1", {"msg": "hi1"}, "val1")
        
        # Tamper with the payload
        self.collection.docs[1]["payload"] = {"msg": "hacked"}
        
        result = validate_chain(self.collection)
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)
        self.assertTrue(any("hash invalid" in e for e in result["errors"]))
