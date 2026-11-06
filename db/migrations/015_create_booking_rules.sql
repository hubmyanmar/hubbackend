CREATE TABLE booking_rules (
    id INTEGER PRIMARY KEY,
    approval_required BOOLEAN NOT NULL DEFAULT TRUE,
    work_start TIME NOT NULL DEFAULT '09:00',
    work_end TIME NOT NULL DEFAULT '18:00',
    notify_email BOOLEAN NOT NULL DEFAULT TRUE,
    notify_in_app BOOLEAN NOT NULL DEFAULT TRUE,
    notify_zoho_cliq BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO booking_rules (
    id,
    approval_required,
    work_start,
    work_end,
    notify_email,
    notify_in_app,
    notify_zoho_cliq
) VALUES (
    1,
    TRUE,
    '09:00',
    '18:00',
    TRUE,
    TRUE,
    TRUE
);
