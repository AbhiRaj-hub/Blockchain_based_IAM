import os
from flask import Flask
from dotenv import load_dotenv
from routes.blocks import blocks_bp
from db.mongo_client import get_blocks_collection
from blockchain.chain import initialize_chain

load_dotenv()

app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017")
app.config["MONGO_DB"] = os.getenv("MONGO_DB", "secureaccess_ledger")
app.config["INGEST_API_KEY"] = os.getenv("INGEST_API_KEY", "dev-ingest-key-change-me")

app.register_blueprint(blocks_bp, url_prefix="/blocks")

@app.before_request
def before_first_request():
    if not hasattr(app, "chain_initialized"):
        collection = get_blocks_collection()
        initialize_chain(collection)
        app.chain_initialized = True

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=port, debug=debug)
