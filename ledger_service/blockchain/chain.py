from .block import Block


def get_latest_block(collection)->Block | None:
    "Get the latest block from the collection"
    data = collection.find_one(sort=[("index", -1)])
    if data:
        return Block.from_dict(data)
    return None


def append_block(collection, event_type: str, payload: dict, validator_id: str)->Block:
    "Append a new block to the chain"
    latest = get_latest_block(collection)
    if not latest:
        raise ValueError("Chain not initialized")
    
    new_block = Block.new(
        index=latest.index + 1,
        event_type=event_type,
        payload=payload,
        previous_hash=latest.hash
    )
    new_block.validator_id = validator_id
    new_block.finalize()
    
    collection.insert_one(new_block.to_dict())
    return new_block


def validate_chain(collection)->dict:
    "Validate the entire chain"
    blocks = list(collection.find(sort=[("index", 1)]))
    errors = []
    
    if not blocks:
        return {"valid": False, "block_count": 0, "errors": ["Chain is empty"]}
        
    previous_block = Block.from_dict(blocks[0])
    if previous_block.hash != previous_block.compute_hash():
        errors.append(f"Genesis block hash invalid")
        
    for i in range(1, len(blocks)):
        current_block = Block.from_dict(blocks[i])
        
        if current_block.index != previous_block.index + 1:
            errors.append(f"Block {current_block.index} index not sequential")
            
        if current_block.previous_hash != previous_block.hash:
            errors.append(f"Block {current_block.index} previous_hash mismatch")
            
        if current_block.hash != current_block.compute_hash():
            errors.append(f"Block {current_block.index} hash invalid")
            
        previous_block = current_block
        
    return {
        "valid": len(errors) == 0,
        "block_count": len(blocks),
        "errors": errors
    }


def initialize_chain(collection):
    "Initialize the chain with genesis block if empty"
    if collection.count_documents({}) == 0:
        genesis = Block.genesis()
        collection.insert_one(genesis.to_dict())
