"""WTQ submission formats: level1.csv (bill_id, json) and level2.csv (bill_id, question_id, question, answer)."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Iterable

from .schema import Answer, Bill


def _n(x: float | None) -> float | int | None:
    if x is None:
        return None
    return int(x) if float(x).is_integer() else round(float(x), 2)


def level1_record(bill: Bill) -> dict[str, Any]:
    """The extraction in the exact WTQ schema."""
    return {
        "provider": bill.provider,
        "bill_month": bill.bill_month,
        "charges": [{"type": c.type, "amount": _n(c.amount)} for c in bill.charges],
        "taxes": [{"type": t.type, "amount": _n(t.amount)} for t in bill.taxes],
        "units_consumed": _n(bill.units_consumed),
        "current_bill": _n(bill.current_bill),
        "payable_within_due_date": _n(bill.payable_within_due_date),
        "payable_after_due_date": _n(bill.payable_after_due_date),
    }


def _csv(header: list[str], rows: Iterable[list[Any]]) -> str:
    buf = io.StringIO(newline="")
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buf.getvalue()


def level1_csv(items: Iterable[tuple[str, Bill | None]]) -> str:
    return _csv(["bill_id", "json"], (
        [bill_id, json.dumps(level1_record(b), ensure_ascii=False) if b else ""] for bill_id, b in items
    ))


def level2_csv(items: Iterable[tuple[str, list[Answer]]]) -> str:
    return _csv(["bill_id", "question_id", "question", "answer"], (
        [bill_id, a.id, a.question, a.answer] for bill_id, answers in items for a in answers
    ))
