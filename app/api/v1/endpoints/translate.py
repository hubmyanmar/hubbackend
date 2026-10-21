import logging
import tempfile
from datetime import date
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.security import get_current_user
from app.models.action_item import ActionItem, ActionItemStatus
from app.models.meeting import Meeting
from app.models.meeting_record import MeetingRecord
from app.models.user import User
from app.schemas.translation import TranslationAccepted, TranslationRequest
from app.services import s3_multipart
from app.services.audio_transcription import MAX_AUDIO_BYTES, transcribe_audio, transcribe_audio_file

logger = logging.getLogger(__name__)


class TranslationValidationRoute(APIRoute):
    """Log request validation errors without including submitted audio URLs."""

    def get_route_handler(self):
        original_handler = super().get_route_handler()

        async def log_validation_errors(request: Request):
            try:
                return await original_handler(request)
            except RequestValidationError as exc:
                errors = [
                    {key: item.get(key) for key in ("loc", "msg", "type")}
                    for item in exc.errors()
                ]
                logger.warning("Translation request validation failed: %s", errors)
                raise

        return log_validation_errors


router = APIRouter(tags=["translation"], route_class=TranslationValidationRoute)


def _process_meeting_audio(
    meeting_id: int,
    task_id: str,
    source_kind: str,
    source_value: str,
) -> None:
    """Run transcription and extraction outside the request, persisting task state."""
    db = None
    try:
        logger.info(
            "Audio task started: meeting_id=%s task_id=%s source_kind=%s",
            meeting_id,
            task_id,
            source_kind,
        )
        db = SessionLocal()
        record = (
            db.query(MeetingRecord)
            .filter(
                MeetingRecord.meeting_id == meeting_id,
                MeetingRecord.task_id == task_id,
            )
            .first()
        )
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if record is None:
            # There is no row left on which to persist a terminal state.
            logger.error(
                "Cannot process meeting audio: record missing for meeting_id=%s task_id=%s",
                meeting_id,
                task_id,
            )
            return
        if meeting is None:
            raise RuntimeError("Meeting no longer exists")

        if source_kind == "s3_object":
            suffix = Path(source_value).suffix or ".audio"
            with tempfile.TemporaryDirectory(prefix="meeting-s3-audio-") as temp_dir:
                local_audio_path = Path(temp_dir) / f"recording{suffix}"
                s3_multipart.download_object_to_file(
                    object_key=source_value,
                    destination=local_audio_path,
                    max_bytes=MAX_AUDIO_BYTES,
                )
                logger.info(
                    "S3 audio downloaded: meeting_id=%s task_id=%s path=%s size_bytes=%s",
                    meeting_id,
                    task_id,
                    local_audio_path,
                    local_audio_path.stat().st_size,
                )
                logger.info("Starting Whisper transcription: meeting_id=%s task_id=%s", meeting_id, task_id)
                transcription_result = transcribe_audio_file(local_audio_path, meeting.meeting_date)
        else:
            logger.info(
                "Starting audio download/transcription: meeting_id=%s task_id=%s",
                meeting_id,
                task_id,
            )
            transcription_result = transcribe_audio(source_value, meeting.meeting_date)
        transcript = transcription_result["transcript"]
        analysis = transcription_result["insights"]
        logger.info(
            "Burmese transcript ready: meeting_id=%s task_id=%s chars=%s preview=%r",
            meeting_id,
            task_id,
            len(transcript),
            " ".join(transcript.split())[:120],
        )
        logger.info("Persisting complete Burmese transcript: meeting_id=%s task_id=%s", meeting_id, task_id)
        record.transcript = transcript
        db.commit()

        logger.info("Saving meeting analysis: meeting_id=%s task_id=%s", meeting_id, task_id)
        record.summary = analysis["summary"]
        record.decisions = analysis["decisions"]
        db.query(ActionItem).filter(ActionItem.meeting_id == meeting_id).delete(synchronize_session=False)
        for item in analysis["action_items"]:
            deadline = item["deadline"]
            due_date = None
            if deadline:
                try:
                    due_date = date.fromisoformat(deadline)
                except ValueError:
                    pass
            db.add(ActionItem(
                meeting_id=meeting_id,
                task=item["task"],
                owner_name=item["assignee"] or "မသတ်မှတ်ရသေး",
                due_date=due_date,
                status=ActionItemStatus.to_do,
            ))
        record.status = "completed"
        record.processing_error = None
        db.commit()
        logger.info("Audio task completed: meeting_id=%s task_id=%s", meeting_id, task_id)
    except Exception as exc:
        if db is not None:
            try:
                db.rollback()
            except Exception:
                logger.exception("Could not roll back failed processing transaction for meeting_id=%s", meeting_id)
        logger.exception("Task failed: meeting_id=%s task_id=%s", meeting_id, task_id)
        failure_db = None
        try:
            # Use a fresh session so a failed transaction/connection in the
            # processing session cannot prevent saving the terminal state.
            failure_db = SessionLocal()
            failed_record = (
                failure_db.query(MeetingRecord)
                .filter(
                    MeetingRecord.meeting_id == meeting_id,
                    MeetingRecord.task_id == task_id,
                )
                .first()
            )
            if failed_record is None:
                logger.error(
                    "Could not persist failed processing state: record missing for meeting_id=%s task_id=%s",
                    meeting_id,
                    task_id,
                )
                return
            failed_record.status = "failed"
            # Store the exception message for diagnostics; the frontend presents
            # a stable, user-friendly retry message instead of exposing details.
            error_text = str(exc).strip() or "No error details were provided."
            failed_record.processing_error = f"{type(exc).__name__}: {error_text}"[:1000]
            failure_db.commit()
        except Exception:
            if failure_db is not None:
                try:
                    failure_db.rollback()
                except Exception:
                    logger.exception(
                        "Could not roll back failure-state transaction for meeting_id=%s",
                        meeting_id,
                    )
            logger.exception(
                "Could not persist failed processing state for meeting_id=%s task_id=%s",
                meeting_id,
                task_id,
            )
        finally:
            if failure_db is not None:
                try:
                    failure_db.close()
                except Exception:
                    logger.exception("Could not close failure-state session for meeting_id=%s", meeting_id)
    finally:
        if db is not None:
            try:
                db.close()
            except Exception:
                logger.exception("Could not close processing session for meeting_id=%s", meeting_id)


@router.post("/translate", response_model=TranslationAccepted, status_code=202)
def process_meeting_audio(
    payload: TranslationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = db.query(Meeting).filter(Meeting.id == payload.meeting_id).first()
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this meeting")

    record = db.query(MeetingRecord).filter(
        MeetingRecord.meeting_id == payload.meeting_id
    ).first()
    if record is None:
        raise HTTPException(status_code=400, detail="Meeting has no uploaded audio")

    if record.audio_object_key:
        expected_prefix = f"audio/{current_user.id}/{meeting.id}/"
        if not record.audio_object_key.startswith(expected_prefix):
            raise HTTPException(status_code=403, detail="Invalid upload object key")
        source_kind, source_value = "s3_object", record.audio_object_key
    else:
        audio_url = payload.audio_url or record.audio_url
        if not audio_url:
            raise HTTPException(status_code=400, detail="Meeting has no audio URL")
        source_kind, source_value = "url", audio_url

    if record.status == "processing" and record.task_id:
        return TranslationAccepted(
            task_id=record.task_id,
            meeting_id=meeting.id,
            status="processing",
        )

    task_id = str(uuid4())
    record.task_id = task_id
    record.status = "processing"
    record.processing_error = None
    db.commit()

    background_tasks.add_task(
        _process_meeting_audio,
        meeting.id,
        task_id,
        source_kind,
        source_value,
    )
    return TranslationAccepted(task_id=task_id, meeting_id=meeting.id, status="processing")
