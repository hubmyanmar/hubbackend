import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import update

from app.core.database import SessionLocal
from app.models.booking_rule import BookingRule
from app.models.meeting_record import MeetingRecord
from app.services import s3_multipart

logger = logging.getLogger(__name__)
RETENTION_SWEEP_INTERVAL_SECONDS = 24 * 60 * 60


def sweep_expired_recordings() -> None:
    db = SessionLocal()
    try:
        rule = db.query(BookingRule).filter(BookingRule.id == 1).first()
        retention_days = rule.retention_days if rule is not None else 90
        if retention_days is None:
            logger.info("Recording retention is set to Never; skipping cleanup")
            return

        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        records = (
            db.query(MeetingRecord)
            .filter(
                MeetingRecord.created_at < cutoff,
                MeetingRecord.audio_object_key.is_not(None),
            )
            .all()
        )
        if not records:
            logger.info("No expired recordings found")
            return

        client = s3_multipart._client()
        bucket = s3_multipart._bucket()
        for record in records:
            try:
                client.delete_object(Bucket=bucket, Key=record.audio_object_key)
                db.execute(
                    update(MeetingRecord)
                    .where(MeetingRecord.id == record.id)
                    .values(audio_object_key=None, audio_url=None)
                )
                db.commit()
                logger.info("Deleted expired recording for meeting record %s", record.id)
            except Exception:
                db.rollback()
                logger.exception(
                    "Failed to delete expired recording for meeting record %s", record.id
                )
    finally:
        db.close()


async def retention_cleanup_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(sweep_expired_recordings)
        except Exception:
            logger.exception("Recording retention sweep failed")
        await asyncio.sleep(RETENTION_SWEEP_INTERVAL_SECONDS)
