from flask import Flask, jsonify

from blockchain.chain import ChainConflictError
from db.mongo_client import get_blocks_collection
from routes.blocks import blocks_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # events are small; reject anything bigger
    app.register_blueprint(blocks_bp)

    @app.get("/health")
    def health():
        try:
            get_blocks_collection().database.command("ping")
        except Exception:  # noqa: BLE001 - any failure means unhealthy
            return jsonify({"status": "unhealthy"}), 503
        return jsonify({"status": "ok", "service": "ledger"})

    @app.errorhandler(ChainConflictError)
    def conflict(_exc):
        return jsonify({"detail": "Ledger busy, retry"}), 503

    @app.errorhandler(413)
    def too_large(_exc):
        return jsonify({"detail": "Payload too large"}), 413

    return app


app = create_app()

if __name__ == "__main__":
    # Local development only. In containers the service runs under gunicorn.
    app.run(host="127.0.0.1", port=5001)
