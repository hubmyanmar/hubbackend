import json
import logging
import math
import os
from datetime import date

import httpx
from dotenv import load_dotenv

from app.services.audio_transcription import AIServiceError

load_dotenv()


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
logger = logging.getLogger(__name__)
LLM_TEXT_CHUNK_CHARS = 3000


def _openrouter_chat(
    messages,
    *,
    json_response=False,
    operation="meeting analysis",
    max_tokens=4000,
):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise AIServiceError("OPENROUTER_API_KEY is not configured")
    model = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")
    payload = {
        "model": model,
        "temperature": 0,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if json_response:
        payload["response_format"] = {"type": "json_object"}

    input_chars = sum(len(str(message.get("content", ""))) for message in messages)
    timeout_seconds = min(300, max(60, 60 + math.ceil(input_chars / 100)))
    raw_data = None
    try:
        with httpx.Client(
            timeout=httpx.Timeout(float(timeout_seconds), connect=20.0)
        ) as client:
            logger.info(
                "Calling OpenRouter: operation=%s model=%s input_chars=%s timeout_seconds=%s",
                operation,
                model,
                input_chars,
                timeout_seconds,
            )
            response = client.post(
                OPENROUTER_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
            raw_data = response.text
            print(
                f"OpenRouter raw response: status_code={response.status_code}, "
                f"body={raw_data}"
            )
            response.raise_for_status()
            result = response.json()
        choice = result["choices"][0]
        content = choice["message"]["content"]
        finish_reason = choice.get("finish_reason")
    except httpx.HTTPStatusError as exc:
        logger.error(f"OpenRouter Error Body: {exc.response.text}")
        print(exc)
        raise AIServiceError(
            f"OpenRouter request failed. Status: {exc.response.status_code}. "
            f"Raw: {exc.response.text}"
        ) from exc
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        print(exc)
        raise AIServiceError(
            f"OpenRouter request failed or returned an invalid response. Raw: {raw_data}"
        ) from exc
    if not isinstance(content, str) or not content.strip():
        raise AIServiceError(f"OpenRouter returned an empty response. Raw: {raw_data}")
    if finish_reason == "length":
        logger.error("OpenRouter response reached its token limit: operation=%s", operation)
        raise AIServiceError(f"OpenRouter truncated its response for {operation}")
    logger.info(
        "OpenRouter returned: operation=%s chars=%s preview=%r",
        operation,
        len(content),
        " ".join(content.split())[:120],
    )
    return content.strip()


def _split_text_preserving_content(text: str, max_chars: int = LLM_TEXT_CHUNK_CHARS) -> list[str]:
    """Split text at whitespace without losing, duplicating, or reordering characters."""
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            boundary = max(text.rfind(" ", start, end), text.rfind("\n", start, end))
            if boundary > start:
                end = boundary + 1
        chunks.append(text[start:end])
        start = end
    if "".join(chunks) != text:
        raise AIServiceError("Transcript chunking did not preserve all source text")
    return chunks


def translate_text_to_burmese(english_text: str) -> str:
    """Translate Whisper's English output into Burmese without summarizing."""
    if not isinstance(english_text, str) or not english_text.strip():
        raise AIServiceError("Cannot translate an empty transcript")
    chunks = _split_text_preserving_content(english_text)
    translations = []
    for index, chunk in enumerate(chunks, start=1):
        logger.info("Translating transcript chunk %s/%s", index, len(chunks))
        translation = _openrouter_chat(
            [
                {
                    "role": "system",
                    "content": (
                        "Translate the provided English text fully and directly into natural Burmese "
                        "(Myanmar language). Do not add headings, summaries, bullet points, or any "
                        "other formatting. Return only the plain Burmese translation. Preserve the "
                        "meaning, names, numbers, dates, repetitions, and uncertainty. Do not add facts."
                    ),
                },
                {"role": "user", "content": chunk.strip()},
            ],
            operation=f"English-to-Burmese translation {index}/{len(chunks)}",
            max_tokens=6000,
        )
        if not translation.strip():
            raise AIServiceError(f"OpenRouter returned empty text for translation chunk {index}/{len(chunks)}")
        translations.append(translation)
    result = "\n".join(translations)
    logger.info("Translated all %s transcript chunks into Burmese", len(translations))
    return result


def extract_meeting_insights(transcript: str, meeting_date: date) -> dict:
    """Extract structured meeting insights from a Burmese transcript."""
    if not isinstance(transcript, str) or not transcript.strip():
        raise AIServiceError("Cannot analyze an empty transcript")
    transcript_chunks = _split_text_preserving_content(transcript)
    summaries = []
    decisions = []
    action_items = []
    for index, chunk in enumerate(transcript_chunks, start=1):
        logger.info("Analyzing Burmese transcript chunk %s/%s", index, len(transcript_chunks))
        content = _openrouter_chat(
            [
                {
                    "role": "system",
                    "content": (
                        "Analyze only the provided meeting transcript section. Return a raw "
                        "JSON object with no Markdown code blocks. All natural-language values must "
                        "be Burmese, except each action item's assignee name, which must be returned "
                        "in English (Latin script) exactly as spoken in the transcript; never "
                        "transliterate names into Burmese. The summary, decisions, and task text must "
                        "be Burmese. The meeting took place on "
                        f"{meeting_date.isoformat()}. Convert relative deadlines using this date. "
                        "Whenever any deadline is mentioned, whether an explicit date or relative "
                        "phrase, return its actual date in YYYY-MM-DD format. Return null for a "
                        "deadline only when no deadline is mentioned at all. Use exactly these keys: "
                        "\"summary\" (string), \"decisions\" "
                        "(array of strings), and \"action_items\" (array of objects with exactly "
                        "\"task\" (string), \"assignee\" (string or null), and \"deadline\" "
                        "(string or null)). Do not omit decisions or action items stated in this "
                        "section. Use null when assignee is not stated. Do not invent facts."
                    ),
                },
                {"role": "user", "content": chunk.strip()},
            ],
            json_response=True,
            operation=f"meeting analysis {index}/{len(transcript_chunks)}",
            max_tokens=4000,
        )
        try:
            result = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIServiceError(f"OpenRouter returned invalid JSON for analysis chunk {index}") from exc
        if not isinstance(result, dict) or set(result) != {"summary", "decisions", "action_items"}:
            raise AIServiceError(f"OpenRouter returned an invalid structure for analysis chunk {index}")

        summary = result.get("summary")
        chunk_decisions = result.get("decisions")
        chunk_items = result.get("action_items")
        if (
            not isinstance(summary, str) or not summary.strip()
            or not isinstance(chunk_decisions, list)
            or not all(isinstance(item, str) for item in chunk_decisions)
            or not isinstance(chunk_items, list)
            or not all(
                isinstance(item, dict)
                and set(item) == {"task", "assignee", "deadline"}
                and isinstance(item.get("task"), str)
                and (item.get("assignee") is None or isinstance(item.get("assignee"), str))
                and (item.get("deadline") is None or isinstance(item.get("deadline"), str))
                for item in chunk_items
            )
        ):
            raise AIServiceError(f"OpenRouter returned invalid fields for analysis chunk {index}")
        summaries.append(summary.strip())
        decisions.extend(chunk_decisions)
        action_items.extend(chunk_items)

    return {
        "summary": "\n".join(summaries),
        "decisions": decisions,
        "action_items": action_items,
    }
