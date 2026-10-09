import unittest
from blockchain.block import Block, hash_payload


class TestBlock(unittest.TestCase):
    def test_genesis_block(self):
        block = Block.genesis()
        self.assertEqual(block.index, 0)
        self.assertEqual(block.event_type, "genesis")
        self.assertEqual(block.previous_hash, "0" * 64)
        self.assertTrue(bool(block.hash))
        self.assertEqual(block.hash, block.compute_hash())

    def test_new_block(self):
        block = Block.new(1, "test", {"msg": "hello"}, "prev")
        self.assertEqual(block.index, 1)
        self.assertEqual(block.event_type, "test")
        self.assertEqual(block.previous_hash, "prev")
        
    def test_compute_hash(self):
        block = Block.new(1, "test", {"msg": "hello"}, "prev")
        block.validator_id = "val1"
        hash1 = block.compute_hash()
        
        block.validator_id = "val2"
        hash2 = block.compute_hash()
        
        self.assertNotEqual(hash1, hash2)

    def test_finalize(self):
        block = Block.new(1, "test", {"msg": "hello"}, "prev")
        self.assertEqual(block.hash, "")
        block.finalize()
        self.assertTrue(bool(block.hash))
        self.assertEqual(block.hash, block.compute_hash())

    def test_to_and_from_dict(self):
        block1 = Block.genesis()
        d = block1.to_dict()
        block2 = Block.from_dict(d)
        
        self.assertEqual(block1.index, block2.index)
        self.assertEqual(block1.hash, block2.hash)
        self.assertEqual(block1.payload, block2.payload)

    def test_hash_payload_determinism(self):
        h1 = hash_payload({"a": 1, "b": 2})
        h2 = hash_payload({"b": 2, "a": 1})
        self.assertEqual(h1, h2)
