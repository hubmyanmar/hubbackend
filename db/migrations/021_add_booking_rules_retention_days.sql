ALTER TABLE booking_rules ADD COLUMN retention_days INTEGER;
UPDATE booking_rules SET retention_days = 90 WHERE retention_days IS NULL;
