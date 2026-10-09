from flask import Blueprint, request, jsonify, current_app
from db.mongo_client import get_blocks_collection
from blockchain.chain import append_block, validate_chain, get_latest_block
from blockchain.consensus import is_authorized_validator

blocks_bp = Blueprint("blocks", __name__)


@blocks_bp.route("", methods=["POST"])
def ingest_block():
    api_key = request.headers.get("X-Api-Key", "")
    expected_key = current_app.config.get("INGEST_API_KEY", "")
    
    if not is_authorized_validator(api_key, expected_key):
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.get_json()
    if not data or "event_type" not in data or "payload" not in data or "validator_id" not in data:
        return jsonify({"error": "Missing fields"}), 400
        
    collection = get_blocks_collection()
    
    try:
        block = append_block(
            collection,
            event_type=data["event_type"],
            payload=data["payload"],
            validator_id=data["validator_id"]
        )
        return jsonify(block.to_dict()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@blocks_bp.route("", methods=["GET"])
def list_blocks():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))
    skip = (page - 1) * page_size
    
    collection = get_blocks_collection()
    total = collection.count_documents({})
    blocks_cursor = collection.find().sort("index", 1).skip(skip).limit(page_size)
    
    blocks = []
    for data in blocks_cursor:
        data.pop("_id", None)
        blocks.append(data)
        
    return jsonify({
        "blocks": blocks,
        "total": total,
        "page": page,
        "page_size": page_size
    }), 200


@blocks_bp.route("/verify", methods=["GET"])
def verify_chain():
    collection = get_blocks_collection()
    result = validate_chain(collection)
    return jsonify(result), 200


@blocks_bp.route("/<int:index>", methods=["GET"])
def get_block(index):
    collection = get_blocks_collection()
    data = collection.find_one({"index": index})
    
    if not data:
        return jsonify({"error": "Block not found"}), 404
        
    data.pop("_id", None)
    return jsonify(data), 200
