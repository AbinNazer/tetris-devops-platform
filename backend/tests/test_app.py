"""
backend/tests/test_app.py
Unit tests for the Tetris backend API.
Run: pytest tests/ -v
"""

import json
import pytest
from unittest.mock import patch, MagicMock

with patch("flask_sqlalchemy.SQLAlchemy.init_app"):
    from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with flask_app.test_client() as c:
        with flask_app.app_context():
            yield c


class TestHealth:
    def test_health_returns_200(self, client):
        with patch("app.db.session.execute"):
            res = client.get("/health")
            assert res.status_code == 200

    def test_health_body_has_status(self, client):
        with patch("app.db.session.execute"):
            data = json.loads(client.get("/health").data)
            assert "status" in data
            assert "database" in data

    def test_health_503_on_db_failure(self, client):
        with patch("app.db.session.execute", side_effect=Exception("DB down")):
            res = client.get("/health")
            assert res.status_code == 503


class TestSaveScore:
    def _post(self, client, payload):
        return client.post("/score", data=json.dumps(payload), content_type="application/json")

    def test_save_valid_score(self, client):
        mock_entry = MagicMock(); mock_entry.id = 1
        with patch("app.db.session.add"), patch("app.db.session.commit"), patch("app.Score") as M:
            M.return_value = mock_entry
            res = self._post(client, {"player_name": "Alice", "score": 5000, "level": 3, "lines": 20})
            assert res.status_code == 201

    def test_save_score_bad_json(self, client):
        res = client.post("/score", data="not json", content_type="application/json")
        assert res.status_code == 400

    def test_save_score_negative_score(self, client):
        res = self._post(client, {"player_name": "Bob", "score": -1})
        assert res.status_code == 400

    def test_save_score_uses_anonymous_default(self, client):
        mock_entry = MagicMock(); mock_entry.id = 2
        with patch("app.db.session.add"), patch("app.db.session.commit"), patch("app.Score") as M:
            M.return_value = mock_entry
            res = self._post(client, {"score": 100})
            assert res.status_code == 201


class TestLeaderboard:
    def _mock_query(self):
        mock_q = MagicMock()
        mock_q.order_by.return_value.limit.return_value.all.return_value = []
        return mock_q

    def test_leaderboard_returns_200(self, client):
        with patch("app.Score.query", self._mock_query()):
            res = client.get("/leaderboard")
            assert res.status_code == 200

    def test_leaderboard_default_limit(self, client):
        mock_q = self._mock_query()
        with patch("app.Score.query", mock_q):
            client.get("/leaderboard")
            mock_q.order_by.return_value.limit.assert_called_with(10)

    def test_leaderboard_custom_limit(self, client):
        mock_q = self._mock_query()
        with patch("app.Score.query", mock_q):
            client.get("/leaderboard?limit=5")
            mock_q.order_by.return_value.limit.assert_called_with(5)

    def test_leaderboard_max_limit_capped_at_50(self, client):
        mock_q = self._mock_query()
        with patch("app.Score.query", mock_q):
            client.get("/leaderboard?limit=999")
            mock_q.order_by.return_value.limit.assert_called_with(50)

    def test_leaderboard_invalid_limit_defaults(self, client):
        mock_q = self._mock_query()
        with patch("app.Score.query", mock_q):
            client.get("/leaderboard?limit=abc")
            mock_q.order_by.return_value.limit.assert_called_with(10)
