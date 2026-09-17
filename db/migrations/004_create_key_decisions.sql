-- Migration: create key_decisions table (PostgreSQL)
-- Stores the primary decisions made during a meeting.

CREATE TABLE IF NOT EXISTS key_decisions (
    id BIGSERIAL PRIMARY KEY,
    meeting_id BIGINT NOT NULL,
    decision_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_key_decisions_meeting FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_key_decisions_meeting_id ON key_decisions(meeting_id);

-- End of migration
