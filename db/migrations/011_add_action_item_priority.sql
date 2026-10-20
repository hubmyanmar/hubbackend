ALTER TABLE action_items
    ADD COLUMN priority VARCHAR(16) NOT NULL DEFAULT 'Medium',
    ADD CONSTRAINT chk_action_items_priority
        CHECK (priority IN ('Low', 'Medium', 'High'));
