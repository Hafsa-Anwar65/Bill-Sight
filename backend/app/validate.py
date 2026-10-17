"""Arithmetic checks that prove an extraction is internally consistent.

A bill is full of totals that must add up. If they do, the numbers were read
correctly; if not, the extractor retries with the failed checks as feedback.
"""

from __future__ import annotations

from .normalize import is_export, shift_month
from .schema import Bill, Check

ROUNDING = 1.0  # bills round the payable amount to whole rupees
CENTS = 0.05


def _fmt(x: float) -> str:
    return f"Rs {x:,.2f}"


def _check(id_: str, label: str, ok: bool, detail: str, critical: bool = False, warn_only: bool = False) -> Check:
    status = "pass" if ok else ("warn" if warn_only else "fail")
    return Check(id=id_, label=label, status=status, detail=detail, critical=critical)


def _skip(id_: str, label: str, why: str) -> Check:
    return Check(id=id_, label=label, status="skip", detail=why)


def run_checks(bill: Bill) -> list[Check]:
    checks: list[Check] = []

    # 1. Required fields --------------------------------------------------- #
    required = {
        "provider": bill.provider,
        "bill_month": bill.bill_month,
        "units_consumed": bill.units_consumed,
        "current_bill": bill.current_bill,
        "payable_within_due_date": bill.payable_within_due_date,
    }
    missing = [k for k, v in required.items() if v is None]
    if not bill.charges:
        missing.append("charges")
    checks.append(_check(
        "required", "Required fields present", not missing,
        "All key fields were read." if not missing else f"Missing: {', '.join(missing)}", critical=True,
    ))

    # 2. Units vs meter readings ------------------------------------------ #
    regs = [r for r in bill.meter_registers if r.previous is not None and r.current is not None]
    if regs and bill.units_consumed is not None:
        mf = bill.multiplier or 1
        diff = {r.name: (r.current - r.previous) * mf for r in regs}  # type: ignore[operator]
        exports = [n for n in diff if is_export(n)]
        imported = sum(v for n, v in diff.items() if n not in exports)
        exported = sum(diff[n] for n in exports)
        # Net-metering bills charge for import − export; time-of-use bills add their registers.
        candidates = {"import − export": imported - exported, "import": imported, "all registers": imported + exported}
        if not exports:
            candidates = {"readings": imported}
        match = next((k for k, v in candidates.items() if abs(v - bill.units_consumed) <= 1.0), None)
        if exports:
            detail = (f"Import {imported:,.2f} − export {exported:,.2f} = {imported - exported:,.2f} units; "
                      f"bill shows {bill.units_consumed:,.0f}.")
        else:
            detail = f"Readings give {imported:,.2f} units; bill shows {bill.units_consumed:,.0f}."
        checks.append(_check("units", "Units match meter readings", match is not None, detail, critical=True))
    else:
        checks.append(_skip("units", "Units match meter readings", "Meter readings not printed."))

    # 3. Printed sub-totals ------------------------------------------------ #
    if bill.printed_total_charges is not None and bill.charges:
        ok = abs(bill.total_charges - bill.printed_total_charges) <= CENTS
        checks.append(_check(
            "charges_total", "Charge lines add up", ok,
            f"Lines sum to {_fmt(bill.total_charges)}; printed total {_fmt(bill.printed_total_charges)}.",
            critical=True,
        ))
    if bill.printed_total_taxes is not None and bill.taxes:
        ok = abs(bill.total_taxes - bill.printed_total_taxes) <= CENTS
        checks.append(_check(
            "taxes_total", "Tax lines add up", ok,
            f"Lines sum to {_fmt(bill.total_taxes)}; printed total {_fmt(bill.printed_total_taxes)}.",
            critical=True,
        ))

    # 4. Current bill = charges + taxes ------------------------------------ #
    if bill.current_bill is not None and bill.charges:
        with_fpa = bill.total_charges + bill.total_taxes
        without_fpa = with_fpa - bill.charges_of("fpa")  # WAPDA bills add FPA after "Current Bill"
        gap_with, gap_without = abs(with_fpa - bill.current_bill), abs(without_fpa - bill.current_bill)
        ok = min(gap_with, gap_without) <= ROUNDING
        fpa_after = bool(bill.charges_of("fpa")) and gap_without < gap_with
        shown = without_fpa if fpa_after else with_fpa
        note = " (fuel adjustment is added after the current bill)" if fpa_after else ""
        checks.append(_check(
            "current_bill", "Current bill = charges + taxes", ok,
            f"Charges + taxes = {_fmt(shown)}{note}; bill shows {_fmt(bill.current_bill)}.",
            critical=True,
        ))

    # 5. Payable reconciles ------------------------------------------------ #
    if bill.payable_within_due_date is not None and bill.charges:
        expected = bill.total_charges + bill.total_taxes + (bill.arrears or 0) + (bill.other_adjustments or 0)
        payable = bill.payable_within_due_date
        ok = abs(expected - payable) <= ROUNDING
        credit_case = expected < 0 and abs(payable) <= ROUNDING  # credit exceeds charges: nothing to pay
        ok = ok or credit_case
        if credit_case:
            detail = (f"Charges + taxes + arrears/adjustments = {_fmt(expected)}. The credit is larger than this "
                      f"month's charges, so nothing is payable and {_fmt(-expected)} carries forward.")
        else:
            detail = f"Charges + taxes + arrears/adjustments = {_fmt(expected)}; payable {_fmt(payable)}."
        checks.append(_check("payable", "Payable amount reconciles", ok, detail, critical=True))

    # 6. Late payment tiers ------------------------------------------------ #
    if bill.late_payment_tiers and bill.payable_within_due_date is not None:
        bad = [
            t for t in bill.late_payment_tiers
            if t.surcharge is not None and abs(bill.payable_within_due_date + t.surcharge - t.total_payable) > ROUNDING
        ]
        checks.append(_check(
            "late", "Late-payment amounts consistent", not bad,
            "Every tier = payable + surcharge." if not bad else
            f"{len(bad)} tier(s) do not equal payable + surcharge.", warn_only=True,
        ))
    else:
        checks.append(_skip("late", "Late-payment amounts consistent", "No late-payment tiers printed."))

    # 7. History ----------------------------------------------------------- #
    if bill.history and bill.bill_month:
        months = [h.month for h in bill.history]
        gaps = [b for a, b in zip(months, months[1:]) if shift_month(a, 1) != b]
        ends_right = months[-1] == shift_month(bill.bill_month, -1)
        ok = not gaps and ends_right
        checks.append(_check(
            "history", "Usage history is complete", ok,
            f"{len(months)} months, {months[0]} to {months[-1]}."
            + (f" Gap before {', '.join(gaps)}." if gaps else "")
            + ("" if ends_right else " Does not end the month before this bill."),
            warn_only=True,
        ))
    else:
        checks.append(_skip("history", "Usage history is complete", "No history printed."))

    # 8. Dates ------------------------------------------------------------- #
    if bill.issue_date and bill.due_date:
        ok = bill.issue_date <= bill.due_date
        checks.append(_check(
            "dates", "Due date after issue date", ok,
            f"Issued {bill.issue_date}, due {bill.due_date}.", warn_only=True,
        ))

    # 9. Billing month matches the issue date ------------------------------ #
    if bill.bill_month and bill.issue_date:
        issued = bill.issue_date[:7]
        ok = issued in (bill.bill_month, shift_month(bill.bill_month, 1), shift_month(bill.bill_month, -1))
        checks.append(_check(
            "month", "Billing month fits the issue date", ok,
            f"Bill month {bill.bill_month}, issued {bill.issue_date}.", warn_only=True,
        ))

    # 10. Fuel adjustment refers to an earlier month ----------------------- #
    if bill.fpa_reference_month and bill.bill_month:
        ok = bill.fpa_reference_month < bill.bill_month
        checks.append(_check(
            "fpa_month", "Fuel adjustment month is in the past", ok,
            f"Adjustment for {bill.fpa_reference_month}, bill for {bill.bill_month}.", warn_only=True,
        ))
    return checks


def failed_critical(checks: list[Check]) -> list[Check]:
    return [c for c in checks if c.critical and c.status == "fail"]


def score(checks: list[Check]) -> tuple[int, int]:
    """(critical failures, total failures + warnings) — lower is better."""
    crit = sum(1 for c in checks if c.critical and c.status == "fail")
    other = sum(1 for c in checks if c.status in ("fail", "warn"))
    return crit, other
