-- Add audio and background-processing columns to existing meeting_records tables.
-- This is additive: legacy audio_url and ai_summary_* columns are preserved.

ALTER TABLE meeting_records
    ADD COLUMN IF NOT EXISTS audio_object_key VARCHAR(1024) NULL,
    ADD COLUMN IF NOT EXISTS ai_summary_en TEXT NULL,
    ADD COLUMN IF NOT EXISTS ai_summary_my TEXT NULL,
    ADD COLUMN IF NOT EXISTS summary TEXT NULL,
    ADD COLUMN IF NOT EXISTS transcript TEXT NULL,
    ADD COLUMN IF NOT EXISTS notes TEXT NULL,
    ADD COLUMN IF NOT EXISTS decisions JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS task_id VARCHAR(36) NULL,
    ADD COLUMN IF NOT EXISTS status VARCHAR(16) NOT NULL DEFAULT 'idle',
    ADD COLUMN IF NOT EXISTS processing_error TEXT NULL;

-- Normalize older bounded text columns without discarding existing content.
ALTER TABLE meeting_records
    ALTER COLUMN transcript TYPE TEXT,
    ALTER COLUMN summary TYPE TEXT;

CREATE INDEX IF NOT EXISTS idx_meeting_records_task_id ON meeting_records(task_id);
