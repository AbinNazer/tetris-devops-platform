"""
backend/app.py
Three-Tier Tetris - Backend API
Flask + PostgreSQL
"""

import os
import logging
import time
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import psycopg2

# ─────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# Database Configuration
# ─────────────────────────────────────────
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "tetrisdb")
DB_USER = os.environ.get("DB_USER", "tetris")
DB_PASS = os.environ.get("DB_PASSWORD", "tetrispassword")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,        # Verify connection before use
    "pool_recycle": 300,          # Recycle connections every 5 min
    "pool_size": 5,
    "max_overflow": 10,
}

db = SQLAlchemy(app)

# ─────────────────────────────────────────
# Prometheus Metrics
# ─────────────────────────────────────────
REQUEST_COUNT = Counter(
    "tetris_request_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "tetris_request_duration_seconds",
    "HTTP request duration",
    ["endpoint"]
)
SCORES_SUBMITTED = Counter(
    "tetris_scores_submitted_total",
    "Total scores submitted"
)

# ─────────────────────────────────────────
# Database Models
# ─────────────────────────────────────────
class Score(db.Model):
    __tablename__ = "scores"

    id          = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(50), nullable=False)
    score       = db.Column(db.Integer, nullable=False, default=0)
    level       = db.Column(db.Integer, nullable=False, default=1)
    lines       = db.Column(db.Integer, nullable=False, default=0)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":          self.id,
            "player_name": self.player_name,
            "score":       self.score,
            "level":       self.level,
            "lines":       self.lines,
            "created_at":  self.created_at.isoformat(),
        }


# ─────────────────────────────────────────
# Middleware — Request Instrumentation
# ─────────────────────────────────────────
@app.before_request
def start_timer():
    request._start_time = time.time()


@app.after_request
def record_metrics(response):
    latency = time.time() - getattr(request, "_start_time", time.time())
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.path,
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(endpoint=request.path).observe(latency)
    return response


# ─────────────────────────────────────────
# Routes
# ─────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint.
    Kubernetes liveness and readiness probes call this.
    Returns 200 if app + DB are reachable, 503 otherwise.
    """
    try:
        db.session.execute(db.text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        logger.error(f"DB health check failed: {e}")
        db_status = "error"

    status = "ok" if db_status == "ok" else "degraded"
    http_code = 200 if status == "ok" else 503

    return jsonify({
        "status":    status,
        "database":  db_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version":   os.environ.get("APP_VERSION", "1.0.0"),
    }), http_code


@app.route("/score", methods=["POST"])
def save_score():
    """
    Save a player score.

    Request body:
        {
            "player_name": "Alice",
            "score": 5000,
            "level": 3,
            "lines": 25
        }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    player_name = str(data.get("player_name", "Anonymous")).strip()[:50]
    score       = int(data.get("score", 0))
    level       = int(data.get("level", 1))
    lines       = int(data.get("lines", 0))

    if score < 0:
        return jsonify({"error": "Score must be non-negative"}), 400

    try:
        entry = Score(
            player_name=player_name,
            score=score,
            level=level,
            lines=lines,
        )
        db.session.add(entry)
        db.session.commit()
        SCORES_SUBMITTED.inc()
        logger.info(f"Score saved: {player_name} → {score}")
        return jsonify({"message": "Score saved", "id": entry.id}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"DB error saving score: {e}")
        return jsonify({"error": "Database error"}), 500


@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    """
    Return top N scores, ordered by score descending.
    Query params:
        limit (int, default 10, max 50)
    """
    try:
        limit = min(int(request.args.get("limit", 10)), 50)
    except ValueError:
        limit = 10

    try:
        entries = (
            Score.query
            .order_by(Score.score.desc())
            .limit(limit)
            .all()
        )
        return jsonify({
            "entries": [e.to_dict() for e in entries],
            "count":   len(entries),
        }), 200
    except SQLAlchemyError as e:
        logger.error(f"DB error fetching leaderboard: {e}")
        return jsonify({"error": "Database error"}), 500


@app.route("/metrics")
def metrics():
    """Expose Prometheus metrics."""
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


# ─────────────────────────────────────────
# Init DB + Run
# ─────────────────────────────────────────
def wait_for_db(retries=10, delay=3):
    """Wait for PostgreSQL to be ready before starting."""
    for attempt in range(1, retries + 1):
        try:
            conn = psycopg2.connect(
                host=DB_HOST, port=DB_PORT,
                dbname=DB_NAME, user=DB_USER, password=DB_PASS,
                connect_timeout=3,
            )
            conn.close()
            logger.info("Database is ready ✓")
            return True
        except Exception as e:
            logger.warning(f"DB not ready (attempt {attempt}/{retries}): {e}")
            time.sleep(delay)
    return False


if __name__ == "__main__":
    if wait_for_db():
        with app.app_context():
            db.create_all()
            logger.info("Database tables created/verified ✓")
    else:
        logger.error("Could not connect to DB after retries. Exiting.")
        raise SystemExit(1)

    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    logger.info(f"Starting Tetris Backend API on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
