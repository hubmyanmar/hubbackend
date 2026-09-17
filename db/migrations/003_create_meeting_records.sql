-- Migration: create meeting_records table (PostgreSQL)
-- Stores one recorded record per meeting, including generated summaries and transcript.

CREATE TABLE IF NOT EXISTS meeting_records (
    id BIGSERIAL PRIMARY KEY,
    meeting_id BIGINT NOT NULL UNIQUE,
    audio_url VARCHAR(255) NULL,
    ai_summary_en TEXT NULL,
    ai_summary_my TEXT NULL,
    transcript TEXT NULL,
    notes TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_meeting_records_meeting FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_meeting_records_meeting_id ON meeting_records(meeting_id);

-- Optional helper trigger so updated_at changes automatically on UPDATE.
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_meeting_records_set_updated_at ON meeting_records;
CREATE TRIGGER trg_meeting_records_set_updated_at
BEFORE UPDATE ON meeting_records
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- End of migration
