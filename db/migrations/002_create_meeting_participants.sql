-- Migration: create meeting_participants table (PostgreSQL)
-- Creates meeting_participants table with FK to meetings(id) and ON DELETE CASCADE
-- Assumes `meetings` table exists and uses BIGINT primary key

CREATE TABLE IF NOT EXISTS meeting_participants (
  id BIGSERIAL PRIMARY KEY,
  meeting_id BIGINT NOT NULL,
  zoho_user_id VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT fk_mp_meeting FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

-- Useful indexes and constraints
CREATE INDEX IF NOT EXISTS idx_meeting_participants_meeting_id ON meeting_participants(meeting_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_meeting_participants_meeting_zoho_user ON meeting_participants(meeting_id, zoho_user_id);
CREATE INDEX IF NOT EXISTS idx_meeting_participants_email ON meeting_participants(email);

-- End of migration
