import pytest

from app.normalize import classify_charge, classify_tax, normalize, parse_date, parse_month
from app.schema import RawExtraction
from tests.conftest import load


@pytest.mark.parametrize("raw, expected", [
    ("2026-04", "2026-04"), ("Apr-2026", "2026-04"), ("SEP 26", "2026-09"), ("Sep-26", "2026-09"),
    ("Sep25", "2025-09"), ("03/26", "2026-03"), ("April 2026", "2026-04"), ("2026-09-24", "2026-09"),
    ("", None), ("garbage", None), ("13/26", None),
])
def test_parse_month(raw, expected):
    assert parse_month(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    ("2026-09-24", "2026-09-24"), ("24 SEP 26", "2026-09-24"), ("06-Apr-2026", "2026-04-06"),
    ("20th Apr 2026", "2026-04-20"), ("28/09/2026", "2026-09-28"), ("31 Feb 26", None), (None, None),
])
def test_parse_date(raw, expected):
    assert parse_date(raw) == expected


@pytest.mark.parametrize("label, expected", [
    ("Fixed Charges", "fixed"), ("Variable Upto 200 Units (Unprotected)", "energy"), ("Variable Peak", "energy"),
    ("Uniform Quarterly Adjustment", "quarterly_adjustment"), ("FCA :Jul-26", "fpa"), ("Total FPA", "fpa"),
    ("FUEL PRICE ADJUSTMENT", "fpa"), ("Additional Surcharge (PHL)", "surcharge"), ("F.C SURCHARGE", "surcharge"),
    ("Subsidies", "subsidy"), ("METER RENT", "meter_rent"), ("COST OF ELECTRICITY", "energy"),
    ("Total Electricity Charges", "energy"),
])
def test_classify_charge(label, expected):
    assert classify_charge(label) == expected


@pytest.mark.parametrize("label, expected", [
    ("Sales Tax u/s 3(1)*", "gst"), ("GST ON FPA", "gst"), ("Electricity Duty", "electricity_duty"),
    ("ED ON FPA", "electricity_duty"), ("MUCT (KMC)", "municipal_tax"), ("Income Tax", "income_tax"),
    ("TV FEE", "other_tax"), ("Taxes", "other_tax"),
])
def test_classify_tax(label, expected):
    assert classify_tax(label) == expected


def test_subsidy_is_negative():
    bill, _ = normalize(RawExtraction.model_validate(load("iesco_2026-09_177")))
    assert bill.charges_of("subsidy") == -1002
    assert bill.total_charges == 7711 - 1002 + 599


def test_provider_and_after_due():
    bill, _ = normalize(RawExtraction.model_validate(load("ke_2026-09_159")))
    assert bill.provider == "KE"
    assert bill.payable_after_due_date == 7939  # first tier = amount right after the due date
    assert [h.month for h in bill.history][-1] == "2026-08"  # current month is not history
    assert len(bill.history) == 12


def test_history_merges_payment_table():
    bill, _ = normalize(RawExtraction.model_validate(load("ke_2026-09_159")))
    aug = next(h for h in bill.history if h.month == "2026-08")
    assert (aug.units, aug.bill_amount, aug.payment) == (235, 11180.07, 11180)


def test_history_months_repaired_when_years_are_wrong():
    data = load("ke_2026-04_286")
    for h in data["usage_history"]:  # model guessed one year for every bar
        h["month"] = "2025-" + h["month"][5:]
    bill, notes = normalize(RawExtraction.model_validate(data))
    assert notes
    assert bill.history[0].month == "2025-04" and bill.history[-1].month == "2026-03"
    assert bill.history[-1].units == 185
