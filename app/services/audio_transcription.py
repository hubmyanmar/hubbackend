import logging
import math
import os
import subprocess
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

MAX_AUDIO_BYTES = 512 * 1024 * 1024
CHUNK_THRESHOLD_BYTES = 20 * 1024 * 1024
CHUNK_SECONDS = 10 * 60
CONTENT_TYPE_EXTENSIONS = {
    "audio/mpeg": "mp3", "audio/mp4": "m4a", "audio/x-m4a": "m4a",
    "audio/wav": "wav", "audio/x-wav": "wav", "audio/ogg": "ogg",
    "audio/webm": "webm", "audio/flac": "flac",
}


class AIServiceError(RuntimeError):
    pass


def _validate_s3_url(audio_url: str) -> None:
    parsed = urlparse(audio_url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (
        hostname.endswith(".amazonaws.com") or hostname.endswith(".amazonaws.com.cn")
    ):
        raise ValueError("audio_url must be a presigned HTTPS S3 URL")


def _transcribe_audio_file(api_key: str, file_path: Path, timeout_seconds: float) -> str:
    """Transcribe an audio chunk with OpenRouter, preserving its spoken language."""
    logger.info("Calling Whisper transcription API: path=%s size_bytes=%s", file_path, file_path.stat().st_size)
    try:
        with file_path.open("rb") as audio_file:
            with httpx.Client(timeout=timeout_seconds) as client:
                response = client.post(
                    "https://openrouter.ai/api/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    data={"model": "openai/whisper-large-v3-turbo"},
                    files={"file": (file_path.name, audio_file, "audio/wav")},
                )
                response.raise_for_status()
                result = response.json()
    except Exception:
        logger.exception("OpenRouter transcription API call failed for audio chunk path=%s", file_path)
        raise
    text = result["text"]
    logger.info(
        "Whisper transcription returned: path=%s chars=%s preview=%r",
        file_path,
        len(text or ""),
        " ".join((text or "").split())[:120],
    )
    return text


def transcribe_audio_file(audio_path: Path, meeting_date: date) -> dict:
    """Return the original-language transcript and structured insights for audio.

    Large recordings are sent to Whisper in sequential chunks before analysis.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise AIServiceError("OPENROUTER_API_KEY is not configured")
    audio_path = Path(audio_path)
    if not audio_path.is_file():
        raise ValueError("Audio file does not exist")
    size = audio_path.stat().st_size
    if size == 0:
        raise ValueError("Audio file is empty")
    if size > MAX_AUDIO_BYTES:
        raise ValueError("Audio file exceeds the 512 MB processing limit")

    transcript_chunks = []
    try:
        # Segment every recording, including highly compressed long files that
        # may be below the byte threshold but exceed a safe audio duration.
        with tempfile.TemporaryDirectory(prefix="meeting-audio-chunks-") as temp_dir:
            chunk_dir = Path(temp_dir)
            output_pattern = chunk_dir / "chunk-%05d.wav"
            logger.info(
                "Splitting audio for complete transcription: path=%s size_bytes=%s segment_seconds=%s",
                audio_path,
                size,
                CHUNK_SECONDS,
            )
            try:
                subprocess.run(
                    [
                        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-i", str(audio_path), "-map", "0:a:0", "-vn",
                        "-f", "segment", "-segment_time", str(CHUNK_SECONDS),
                        "-reset_timestamps", "1", "-c:a", "pcm_s16le",
                        "-ar", "16000", "-ac", "1", str(output_pattern),
                    ],
                    check=True,
                    capture_output=True,
                    timeout=3 * 60 * 60,
                )
            except FileNotFoundError as exc:
                raise AIServiceError("ffmpeg is required to split audio for transcription") from exc
            except subprocess.TimeoutExpired as exc:
                raise AIServiceError("Audio chunking exceeded its three-hour processing limit") from exc
            except subprocess.CalledProcessError as exc:
                logger.error("ffmpeg chunking failed: %s", exc.stderr.decode(errors="replace")[-2000:])
                raise AIServiceError("Could not split the uploaded audio into transcription chunks") from exc

            chunk_paths = sorted(chunk_dir.glob("chunk-*.wav"))
            if not chunk_paths:
                raise AIServiceError("Audio chunking did not produce any transcription chunks")
            largest_chunk_bytes = max(path.stat().st_size for path in chunk_paths)
            if any(path.stat().st_size == 0 for path in chunk_paths):
                raise AIServiceError("Audio chunking produced an empty chunk")
            if largest_chunk_bytes > CHUNK_THRESHOLD_BYTES:
                raise AIServiceError("A generated audio chunk exceeds the 20 MB Whisper limit")

            # Give larger chunks more time, while bounding each Whisper request.
            timeout_seconds = min(
                600,
                max(120, 120 + math.ceil(largest_chunk_bytes / (1024 * 1024)) * 20),
            )
            logger.info(
                "Audio split into %s chunks; largest_chunk_bytes=%s whisper_timeout_seconds=%s",
                len(chunk_paths),
                largest_chunk_bytes,
                timeout_seconds,
            )
            for index, chunk_path in enumerate(chunk_paths, start=1):
                logger.info(
                    "Sending Whisper chunk %s/%s: path=%s size_bytes=%s",
                    index,
                    len(chunk_paths),
                    chunk_path,
                    chunk_path.stat().st_size,
                )
                chunk_text = _transcribe_audio_file(api_key, chunk_path, float(timeout_seconds))
                if not isinstance(chunk_text, str) or not chunk_text.strip():
                    raise AIServiceError("Whisper returned empty text")
                transcript_chunks.append(chunk_text.strip())
                logger.info("Whisper chunk %s/%s succeeded", index, len(chunk_paths))
        transcript_text = "\n".join(transcript_chunks)
    except AIServiceError:
        raise
    except Exception as exc:
        raise AIServiceError("OpenRouter Whisper transcription request failed") from exc

    if len(transcript_chunks) == 0 or not isinstance(transcript_text, str) or not transcript_text.strip():
        raise AIServiceError("Whisper returned an empty transcription")

    # Import locally to avoid a module cycle: meeting_ai uses AIServiceError
    # from this module for its API error reporting.
    from app.services.meeting_ai import extract_meeting_insights

    transcript = transcript_text.strip()
    try:
        insights = extract_meeting_insights(transcript, meeting_date)
    except Exception:
        logger.exception("Meeting insight extraction failed")
        raise
    return {"transcript": transcript, "insights": insights}


def transcribe_audio(audio_url: str, meeting_date: date) -> dict:
    """Fetch a legacy presigned URL to a temp file, then transcribe locally."""
    _validate_s3_url(audio_url)
    try:
        with tempfile.TemporaryDirectory(prefix="meeting-audio-download-") as temp_dir:
            with httpx.Client(timeout=120.0, follow_redirects=False) as http_client:
                with http_client.stream("GET", audio_url) as audio_response:
                    audio_response.raise_for_status()
                    content_type = audio_response.headers.get("content-type", "").split(";")[0].lower()
                    extension = CONTENT_TYPE_EXTENSIONS.get(content_type, "mp3")
                    audio_path = Path(temp_dir) / f"meeting-audio.{extension}"
                    size = 0
                    with audio_path.open("wb") as audio_file:
                        for chunk in audio_response.iter_bytes():
                            size += len(chunk)
                            if size > MAX_AUDIO_BYTES:
                                raise ValueError("Audio file exceeds the 512 MB processing limit")
                            audio_file.write(chunk)
            return transcribe_audio_file(audio_path, meeting_date)
    except (httpx.HTTPError, ValueError) as exc:
        if isinstance(exc, ValueError):
            raise
        raise AIServiceError("Audio download or transcription request failed") from exc
