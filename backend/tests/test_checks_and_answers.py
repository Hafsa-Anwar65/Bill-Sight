import pytest

from app.analysis import QUESTIONS, answer_all, summary
from app.normalize import normalize
from app.schema import RawExtraction
from app.validate import failed_critical, run_checks
from tests.conftest import ALL, load


def bill_of(name):
    return normalize(RawExtraction.model_validate(load(name)))[0]


@pytest.mark.parametrize("name", ALL)
def test_ground_truth_passes_every_check(name):
    checks = run_checks(bill_of(name))
    assert [c for c in checks if c.status in ("fail", "warn")] == []


@pytest.mark.parametrize("name", ALL)
def test_twelve_answers(name):
    answers = answer_all(bill_of(name))
    assert [a.question for a in answers] == QUESTIONS
    assert all(a.answer and "could not be worked out" not in a.answer for a in answers)


def test_wrong_digit_is_caught():
    data = load("ke_2026-09_159")
    data["charges"][1]["amount"] = 4569.69  # 96 read as 69
    assert {c.id for c in failed_critical(run_checks(normalize(RawExtraction.model_validate(data))[0]))} >= {"charges_total"}


def test_handwritten_adjustment_is_caught():
    data = load("iesco_2026-08_676")
    data["other_adjustments"] = -21565  # the pen note on the paper bill
    assert "payable" in {c.id for c in failed_critical(run_checks(normalize(RawExtraction.model_validate(data))[0]))}


EXPECTED = {
    ("ke_2026-09_159", "Q2"): ["Jul 2026", "298 units"],
    ("ke_2026-09_159", "Q3"): ["Rs 613.31", "Jul 2026"],
    ("ke_2026-09_159", "Q4"): ["Rs 317.96", "Rs 7,939", "Rs 635.92", "Rs 8,257"],
    ("ke_2026-09_159", "Q5"): ["No.", "159", "176", "Sep 2025"],
    ("ke_2026-09_159", "Q8"): ["Yes.", "3 months"],
    ("ke_2026-09_159", "Q9"): ["Down.", "298", "235", "159"],
    ("iesco_2026-08_676", "Q8"): ["No.", "Sep 2025", "Feb 2026", "Mar 2026", "May 2026", "Jul 2026", "Rs 31,203"],
    ("iesco_2026-08_676", "Q3"): ["Rs 370.76", "Jun 2026"],
    ("iesco_2026-09_177", "Q5"): ["Yes.", "177", "172"],
    ("iesco_2026-09_177", "Q8"): ["May 2026", "1 of 12"],
    ("iesco_2026-09_58", "Q8"): ["Yes."],
    ("ke_2026-04_286", "Q1"): ["standard", "Off Peak, Peak"],
    ("ke_2026-04_286", "Q2"): ["Jun 2025", "438"],
    ("ke_2026-04_286", "Q7"): ["393 more units", "Jun 2025 – Aug 2025", "Dec 2025 – Feb 2026"],
}


@pytest.mark.parametrize("key", list(EXPECTED))
def test_answer_contents(key):
    name, qid = key
    answer = next(a for a in answer_all(bill_of(name)) if a.id == qid).answer
    for part in EXPECTED[key]:
        assert part in answer, f"{qid}: {part!r} not in {answer!r}"


def test_summary_numbers():
    s = summary(bill_of("ke_2026-09_159"))
    assert s["month_cost"] == 7620.53
    assert s["average_cost_per_unit"] == 47.93
    assert s["late_fee_if_paid_late"] == 317.96
    assert s["series"][-1] == {"month": "2026-09", "units": 159.0, "bill_amount": 7620.53, "current": True}
