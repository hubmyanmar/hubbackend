-- Migration: create action_items table (PostgreSQL)
-- Stores tasks or action items discussed during a meeting.

CREATE TYPE action_item_status AS ENUM ('to_do', 'in_progress', 'complete');

CREATE TABLE IF NOT EXISTS action_items (
    id BIGSERIAL PRIMARY KEY,
    meeting_id BIGINT NOT NULL,
    task VARCHAR(255) NOT NULL,
    owner_name VARCHAR(255) NOT NULL,
    due_date DATE NULL,
    status action_item_status NOT NULL DEFAULT 'to_do',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_action_items_meeting FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_action_items_meeting_id ON action_items(meeting_id);
CREATE INDEX IF NOT EXISTS idx_action_items_status ON action_items(status);

CREATE OR REPLACE FUNCTION set_action_items_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_action_items_set_updated_at ON action_items;
CREATE TRIGGER trg_action_items_set_updated_at
BEFORE UPDATE ON action_items
FOR EACH ROW
EXECUTE FUNCTION set_action_items_updated_at();

-- End of migration
