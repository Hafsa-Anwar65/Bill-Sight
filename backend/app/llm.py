"""Thin wrapper around the Gemini API: deterministic settings, retries, JSON parsing."""

from __future__ import annotations

import io
import json
import re
import time
from functools import lru_cache
from typing import Any

from PIL import Image, ImageOps

from .config import settings


class LLMError(RuntimeError):
    """Raised with a message that is safe to show to the user."""


RETRYABLE = {429, 500, 502, 503, 504}
MAX_SIDE = 2560


def model_name() -> str:
    return settings.model


@lru_cache(maxsize=1)
def _client():
    if not settings.api_key:
        raise LLMError("GEMINI_API_KEY is not set. Add it to the .env file in the project root.")
    from google import genai

    return genai.Client(api_key=settings.api_key)


def prepare_image(data: bytes) -> bytes:
    """Fix phone-photo rotation, drop alpha, cap size. Returns JPEG bytes."""
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img).convert("RGB")
    except Exception as exc:  # noqa: BLE001 - any decode failure means a bad upload
        raise LLMError("This file is not a readable image (use PNG or JPG).") from exc
    if max(img.size) > MAX_SIDE:
        img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=92)
    return out.getvalue()


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fenced:
        text = fenced.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            return json.loads(match.group(0))
        raise


def _call(contents: list[Any], config: Any, retries: int = 4):
    from google.genai import errors

    delay = 2.0
    for attempt in range(retries):
        try:
            return _client().models.generate_content(model=settings.model, contents=contents, config=config)
        except errors.APIError as exc:
            code = getattr(exc, "code", None)
            if code in RETRYABLE and attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            if code == 404:
                raise LLMError(f"Model '{settings.model}' was not found. Check LLM_MODEL in .env.") from exc
            if code in (400, 401, 403) and "key" in str(exc).lower():
                raise LLMError("The Gemini API key was rejected. Check GEMINI_API_KEY in .env.") from exc
            raise LLMError(f"Gemini error {code}: {exc}") from exc
        except (ConnectionError, TimeoutError, OSError) as exc:
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise LLMError("Could not reach the Gemini API. Check your internet connection.") from exc
    raise LLMError("Gemini did not respond after several retries.")


def generate_json(prompt: str, image_jpeg: bytes | None = None, schema: Any = None) -> dict[str, Any]:
    from google.genai import types

    contents: list[Any] = []
    if image_jpeg is not None:
        contents.append(types.Part.from_bytes(data=image_jpeg, mime_type="image/jpeg"))
    contents.append(prompt)
    config = types.GenerateContentConfig(
        temperature=settings.temperature,
        seed=settings.seed,
        response_mime_type="application/json",
        response_schema=schema,
    )
    response = _call(contents, config)
    parsed = getattr(response, "parsed", None)
    if parsed is not None:
        return parsed.model_dump() if hasattr(parsed, "model_dump") else parsed
    try:
        return _parse_json(response.text or "")
    except (json.JSONDecodeError, TypeError) as exc:
        raise LLMError("The model returned invalid JSON.") from exc


def generate_text(prompt: str) -> str:
    from google.genai import types

    config = types.GenerateContentConfig(temperature=settings.temperature, seed=settings.seed)
    response = _call([prompt], config)
    return (response.text or "").strip()
