"""Bill image -> validated `Bill`.

Flow: read with the vision model -> normalize -> run arithmetic checks ->
if a critical check fails, re-read with the failures as feedback -> keep the
best attempt.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from pydantic import ValidationError

from . import cache, llm
from .config import settings
from .normalize import normalize
from .prompts import EXTRACTION_PROMPT, RETRY_PROMPT
from .schema import Bill, Check, RawExtraction
from .validate import failed_critical, run_checks, score

Reader = Callable[[str, bytes, str], dict[str, Any]]


@dataclass
class ExtractionResult:
    bill: Bill
    checks: list[Check]
    attempts: int
    image_hash: str
    cached: bool = False
    notes: list[str] = field(default_factory=list)


def _gemini_reader(prompt: str, document: bytes, mime: str) -> dict[str, Any]:
    return llm.generate_json(prompt, document=document, mime=mime, schema=RawExtraction)


def extract_bill(data: bytes, use_cache: bool = True, reader: Reader | None = None) -> ExtractionResult:
    key = cache.image_hash(data)
    if use_cache and (hit := cache.get(key)):
        bill = Bill.model_validate(hit["bill"])
        return ExtractionResult(bill, run_checks(bill), hit.get("attempts", 1), key, cached=True, notes=hit.get("notes", []))

    read = reader or _gemini_reader
    document, mime = llm.prepare_document(data)
    prompt = EXTRACTION_PROMPT
    best: tuple[tuple[int, int], Bill, list[Check], list[str]] | None = None
    attempts = 0

    for attempts in range(1, settings.max_attempts + 1):
        try:
            raw = RawExtraction.model_validate(read(prompt, document, mime))
        except (ValidationError, llm.LLMError) as exc:
            if isinstance(exc, llm.LLMError) and "invalid JSON" not in str(exc):
                raise  # config / network problems: retrying the read will not help
            continue

        bill, notes = normalize(raw)
        checks = run_checks(bill)
        if best is None or score(checks) < best[0]:
            best = (score(checks), bill, checks, notes)

        failures = failed_critical(checks) or [c for c in checks if c.status in ("fail", "warn")]
        if not failures or (not failed_critical(checks) and attempts >= 2):
            break  # clean, or only soft warnings after a second look
        prompt = "\n\n".join([
            EXTRACTION_PROMPT,
            RETRY_PROMPT.format(failures="\n".join(f"- {c.label}: {c.detail}" for c in failures)),
            "Previous JSON:\n" + json.dumps(raw.model_dump(), ensure_ascii=False),
        ])

    if best is None:
        raise llm.LLMError("Could not read this bill. Try a clearer, straight, well-lit photo.")

    _, bill, checks, notes = best
    if not failed_critical(checks):
        cache.put(key, {"bill": bill.model_dump(), "attempts": attempts, "notes": notes})
    return ExtractionResult(bill, checks, attempts, key, notes=notes)
