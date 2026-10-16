"""The pipeline shared by the web API and the batch CLI."""

from __future__ import annotations

import json
import re
from typing import Any

from . import llm
from .analysis import answer_all, insights, summary
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
        "insights": insights(bill),
    }


_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _numbers(text: str) -> set[float]:
    out = set()
    for m in _NUM.findall(text):
        try:
            out.add(round(float(m.replace(",", "")), 2))
        except ValueError:
            pass
    return out


def _unverified(answer: str, source: str) -> list[float]:
    """Numbers in the answer that do not appear in the source (ignores small counts like 3 or 12)."""
    known = _numbers(source)
    known |= {round(k) for k in known} | {round(k, 1) for k in known}
    return [n for n in _numbers(answer) if n > 31 and n not in known and round(n) not in known]


def ask(bill: Bill, question: str) -> str:
    facts = summary(bill)
    facts.pop("series", None)
    facts["answers"] = {a.question: a.answer for a in answer_all(bill)}
    prompt = ASK_PROMPT.format(
        bill=json.dumps(bill.model_dump(), ensure_ascii=False),
        facts=json.dumps(facts, ensure_ascii=False),
        question=question.strip(),
    )
    source = prompt
    answer = llm.generate_text(prompt)
    bad = _unverified(answer, source)
    if bad:  # one corrective pass: the model must only use numbers from the data
        answer = llm.generate_text(
            prompt + "\n\nYour previous answer used numbers that are not in the data: "
            + ", ".join(f"{b:g}" for b in bad) + ". Answer again using only numbers from BILL and FACTS."
        )
        if _unverified(answer, source):
            answer += "\n\n(Some figures above are estimates; check them against the bill.)"
    return answer
