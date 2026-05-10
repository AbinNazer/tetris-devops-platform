CREATE TABLE IF NOT EXISTS scores (
    id          SERIAL PRIMARY KEY,
    player_name VARCHAR(50)  NOT NULL,
    score       INTEGER      NOT NULL DEFAULT 0,
    level       INTEGER      NOT NULL DEFAULT 1,
    lines       INTEGER      NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Index for fast leaderboard queries
CREATE INDEX IF NOT EXISTS idx_scores_score_desc ON scores (score DESC);

-- Seed data for testing
INSERT INTO scores (player_name, score, level, lines) VALUES
    ('DevOps Dan',   15000, 8, 80),
    ('K8s Karen',    12500, 7, 65),
    ('Docker Dave',  10000, 6, 50),
    ('Argo Alice',    8000, 5, 40),
    ('Grafana Grace', 5000, 4, 25);
