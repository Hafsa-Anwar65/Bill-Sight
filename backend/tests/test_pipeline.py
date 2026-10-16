import csv
import io
import json

from fastapi.testclient import TestClient

from app import extract
from app.export import level1_csv, level1_record, level2_csv
from app.analysis import answer_all
from app.normalize import normalize
from app.schema import RawExtraction
from tests.conftest import ALL, load


def test_retry_fixes_a_bad_read(png_bytes):
    good = load("ke_2026-09_459")
    bad = json.loads(json.dumps(good))
    bad["taxes"][1]["amount"] = 3381.98
    calls = []

    def reader(prompt, jpeg):
        calls.append(prompt)
        return bad if len(calls) == 1 else good

    result = extract.extract_bill(png_bytes, use_cache=False, reader=reader)
    assert result.attempts == 2
    assert "Tax lines add up" in calls[1]  # feedback reached the model
    assert result.bill.total_taxes == 4256.81


def test_cache_hit(png_bytes):
    n = []
    reader = lambda p, j: n.append(1) or load("iesco_2026-09_58")  # noqa: E731
    extract.extract_bill(png_bytes, reader=reader)
    again = extract.extract_bill(png_bytes, reader=reader)
    assert again.cached and len(n) == 1


def test_level1_record_schema():
    rec = level1_record(normalize(RawExtraction.model_validate(load("iesco_2026-09_177")))[0])
    assert list(rec) == ["provider", "bill_month", "charges", "taxes", "units_consumed",
                         "current_bill", "payable_within_due_date", "payable_after_due_date"]
    assert rec["charges"] == [{"type": "energy", "amount": 7711}, {"type": "subsidy", "amount": -1002},
                              {"type": "fpa", "amount": 599}]
    assert rec["payable_within_due_date"] == 8603 and rec["payable_after_due_date"] == 8939


def test_csvs_have_no_blank_rows_and_parse():
    bills = [(n, normalize(RawExtraction.model_validate(load(n)))[0]) for n in ALL]
    l1 = level1_csv(bills)
    l2 = level2_csv([(n, answer_all(b)) for n, b in bills])
    assert "\n\n" not in l1 and "\r" not in l1
    rows = list(csv.DictReader(io.StringIO(l1)))
    assert len(rows) == len(ALL) and all(json.loads(r["json"])["provider"] for r in rows)
    qa = list(csv.DictReader(io.StringIO(l2)))
    assert len(qa) == 12 * len(ALL) and {r["question_id"] for r in qa} == {f"Q{i}" for i in range(1, 13)}


def test_api_round_trip(png_bytes, monkeypatch):
    from app.api import app

    monkeypatch.setattr(extract, "_gemini_reader", lambda p, j: load("ke_2026-09_159"))
    client = TestClient(app)
    assert client.get("/api/health").json()["ok"]

    res = client.post("/api/analyze", files={"file": ("KESC_0002.png", png_bytes, "image/png")})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["bill_id"] == "KESC_0002" and len(body["answers"]) == 12
    assert body["level1"]["payable_within_due_date"] == 7621

    exp = client.post("/api/export", json={"items": [{"bill_id": "KESC_0002", "bill": body["bill"]}]}).json()
    assert exp["level1_csv"].startswith("bill_id,json\nKESC_0002,")
    assert exp["level2_csv"].count("\nKESC_0002,Q") == 12

    assert client.post("/api/analyze", files={"file": ("x.pdf", b"%PDF", "application/pdf")}).status_code == 415
