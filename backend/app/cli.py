"""Batch mode: every bill image in a folder -> output/level1.csv + output/level2.csv.

    python -m app.cli ../bills --out ../output
    python -m app.cli ../bills --ids ../level1_template.csv   # keep the official row order
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import llm, service
from .export import level1_csv, level2_csv
from .schema import Answer, Bill

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def _ids_from(template: Path) -> list[str]:
    with template.open(newline="", encoding="utf-8-sig") as fh:
        return [row["bill_id"].strip() for row in csv.DictReader(fh) if row.get("bill_id", "").strip()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bills", type=Path, help="folder with bill images (file name = bill_id)")
    ap.add_argument("--out", type=Path, default=Path("output"))
    ap.add_argument("--ids", type=Path, help="CSV with a bill_id column; output follows its order")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args(argv)

    files = {p.stem: p for p in sorted(args.bills.iterdir()) if p.suffix.lower() in IMAGE_EXT}
    order = _ids_from(args.ids) if args.ids else list(files)
    missing = [i for i in order if i not in files]
    if not files:
        print(f"No images found in {args.bills}", file=sys.stderr)
        return 1

    def run(bill_id: str) -> tuple[str, dict | None, str | None]:
        try:
            return bill_id, service.analyze(files[bill_id].read_bytes(), bill_id, use_cache=not args.no_cache), None
        except llm.LLMError as exc:
            return bill_id, None, str(exc)

    todo = [i for i in order if i in files]
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        results = {bid: (res, err) for bid, res, err in pool.map(run, todo)}

    l1: list[tuple[str, Bill | None]] = []
    l2: list[tuple[str, list[Answer]]] = []
    report = []
    for bill_id in order:
        res, err = results.get(bill_id, (None, "image not found"))
        if res is None:
            print(f"  FAIL  {bill_id}: {err}")
            l1.append((bill_id, None))
            report.append({"bill_id": bill_id, "error": err})
            continue
        bill = Bill.model_validate(res["bill"])
        l1.append((bill_id, bill))
        l2.append((bill_id, [Answer.model_validate(a) for a in res["answers"]]))
        bad = [c["label"] for c in res["checks"] if c["status"] in ("fail", "warn")]
        units = f"{bill.units_consumed:g}" if bill.units_consumed is not None else "?"
        payable = f"{bill.payable_within_due_date:,.0f}" if bill.payable_within_due_date is not None else "?"
        print(f"  {'OK  ' if not bad else 'WARN'}  {bill_id}: {bill.provider} {bill.bill_month}, "
              f"{units} units, payable Rs {payable}"
              + (f"  [check: {', '.join(bad)}]" if bad else ""))
        report.append({"bill_id": bill_id, "attempts": res["attempts"], "checks": res["checks"]})

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "level1.csv").write_text(level1_csv(l1), encoding="utf-8", newline="")
    (args.out / "level2.csv").write_text(level2_csv(l2), encoding="utf-8", newline="")
    (args.out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {args.out / 'level1.csv'} ({len(l1)} rows) and {args.out / 'level2.csv'} ({sum(len(a) for _, a in l2)} rows).")
    if missing:
        print(f"Missing images for: {', '.join(missing)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
