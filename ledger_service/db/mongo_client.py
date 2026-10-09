from flask import current_app
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

_client = None

def get_database()->Database:
    global _client
    if _client is None:
        uri = current_app.config.get("MONGO_URI")
        _client = MongoClient(uri)
    db_name = current_app.config.get("MONGO_DB")
    return _client[db_name]

def get_blocks_collection()->Collection:
    db = get_database()
    collection = db["blocks"]
    collection.create_index("index", unique=True)
    return collection
