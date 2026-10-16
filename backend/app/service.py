"""The pipeline shared by the web API and the batch CLI."""

from __future__ import annotations

import json
from typing import Any

from . import llm
from .analysis import answer_all, summary
from .export import level1_record
from .extract import Reader, extract_bill
from .prompts import ASK_PROMPT
from .schema import Bill


def analyze(data: bytes, bill_id: str, use_cache: bool = True, reader: Reader | None = None) -> dict[str, Any]:
    result = extract_bill(data, use_cache=use_cache, reader=reader)
    bill = result.bill
    return {
        "bill_id": bill_id,
        "image_hash": result.image_hash,
        "attempts": result.attempts,
        "cached": result.cached,
        "notes": result.notes,
        "bill": bill.model_dump(),
        "level1": level1_record(bill),
        "checks": [c.model_dump() for c in result.checks],
        "answers": [a.model_dump() for a in answer_all(bill)],
        "summary": summary(bill),
    }


def ask(bill: Bill, question: str) -> str:
    facts = summary(bill)
    facts.pop("series", None)
    facts["answers"] = {a.question: a.answer for a in answer_all(bill)}
    prompt = ASK_PROMPT.format(
        bill=json.dumps(bill.model_dump(), ensure_ascii=False),
        facts=json.dumps(facts, ensure_ascii=False),
        question=question.strip(),
    )
    return llm.generate_text(prompt)
