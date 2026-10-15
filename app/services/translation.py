import os

import httpx


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def translate_text(text: str, source_language: str, target_language: str) -> str:
    """Translate text with OpenRouter using the configured API key and model."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")

    model = os.getenv("OPENROUTER_MODEL", "openrouter/auto")
    source_description = "the detected source language" if source_language == "auto" else source_language
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a translation engine. Translate the user's text from "
                    f"{source_description} into {target_language}. Preserve its meaning and tone. "
                    "Return only the translated text, without commentary or quotation marks."
                ),
            },
            {"role": "user", "content": text},
        ],
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    with httpx.Client(timeout=45.0) as client:
        response = client.post(OPENROUTER_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

    try:
        translated = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("OpenRouter returned an invalid response") from exc
    if not isinstance(translated, str) or not translated.strip():
        raise RuntimeError("OpenRouter returned an empty translation")
    return translated.strip()
