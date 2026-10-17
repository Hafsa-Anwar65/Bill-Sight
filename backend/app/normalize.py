"""Turn the model's raw output into a clean `Bill`.

Everything here is deterministic: dates and months are re-parsed, line types are
re-classified from their printed labels, signs are fixed, and the usage history
is merged, de-duplicated and sorted. The model reads the bill; Python decides
what the numbers mean.
"""

from __future__ import annotations

import re
from datetime import date

from .schema import (
    CHARGE_TYPES,
    TAX_TYPES,
    Bill,
    HistoryEntry,
    LateTier,
    LineItem,
    MeterRegister,
    NetMetering,
    RawExtraction,
)

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1
)}

PROVIDER_ALIASES = {
    "KE": ("K-ELECTRIC", "K ELECTRIC", "KELECTRIC", "KESC", "KARACHI ELECTRIC", "KE"),
    "IESCO": ("IESCO", "ISLAMABAD ELECTRIC"),
    "LESCO": ("LESCO", "LAHORE ELECTRIC"),
    "GEPCO": ("GEPCO", "GUJRANWALA ELECTRIC"),
    "FESCO": ("FESCO", "FAISALABAD ELECTRIC"),
    "MEPCO": ("MEPCO", "MULTAN ELECTRIC"),
    "PESCO": ("PESCO", "PESHAWAR ELECTRIC"),
    "HESCO": ("HESCO", "HYDERABAD ELECTRIC"),
    "SEPCO": ("SEPCO", "SUKKUR ELECTRIC"),
    "QESCO": ("QESCO", "QUETTA ELECTRIC"),
    "TESCO": ("TESCO", "TRIBAL ELECTRIC"),
}


# --------------------------------------------------------------------------- #
# Dates and months
# --------------------------------------------------------------------------- #
def _year(token: str) -> int | None:
    if not token.isdigit():
        return None
    y = int(token)
    if len(token) == 2:
        y += 2000
    return y if 2000 <= y <= 2099 else None


def parse_month(value: str | None) -> str | None:
    """Accepts '2026-04', 'Apr-2026', 'SEP 26', 'Sep25', '03/26', 'April 2026' → 'YYYY-MM'."""
    if not value:
        return None
    s = str(value).strip().lower()

    m = re.fullmatch(r"(\d{4})[-/](\d{1,2})(?:[-/]\d{1,2})?", s)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        return f"{y:04d}-{mo:02d}" if 1 <= mo <= 12 else None

    m = re.fullmatch(r"(\d{1,2})[-/ ](\d{2}|\d{4})", s)
    if m:
        mo, y = int(m.group(1)), _year(m.group(2))
        return f"{y:04d}-{mo:02d}" if y and 1 <= mo <= 12 else None

    m = re.fullmatch(r"([a-z]{3})[a-z]*[\s\-/,']*(\d{2}|\d{4})", s)
    if m and m.group(1) in MONTHS:
        y = _year(m.group(2))
        return f"{y:04d}-{MONTHS[m.group(1)]:02d}" if y else None
    return None


def parse_date(value: str | None) -> str | None:
    """Accepts '2026-09-24', '24 SEP 26', '06-Apr-2026', '20th Apr 2026' → 'YYYY-MM-DD'."""
    if not value:
        return None
    s = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", str(value).strip().lower())

    def build(y: int | None, mo: int, d: int) -> str | None:
        try:
            return date(y, mo, d).isoformat() if y else None
        except ValueError:
            return None

    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        return build(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.fullmatch(r"(\d{1,2})[\s\-/.]+([a-z]{3})[a-z]*[\s\-/.,]+(\d{2}|\d{4})", s)
    if m and m.group(2) in MONTHS:
        return build(_year(m.group(3)), MONTHS[m.group(2)], int(m.group(1)))
    m = re.fullmatch(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2}|\d{4})", s)
    if m:
        return build(_year(m.group(3)), int(m.group(2)), int(m.group(1)))
    return None


def is_export(register_name: str) -> bool:
    return bool(re.search(r"export|\bexp\b|\(e\)|delivered|solar\s*gen", register_name.lower()))


def shift_month(month: str, delta: int) -> str:
    y, m = map(int, month.split("-"))
    total = y * 12 + (m - 1) + delta
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def month_label(month: str) -> str:
    y, m = map(int, month.split("-"))
    return f"{date(y, m, 1):%b %Y}"


# --------------------------------------------------------------------------- #
# Line classification
# --------------------------------------------------------------------------- #
_CHARGE_RULES: list[tuple[str, str]] = [
    (r"subsid", "subsidy"),
    (r"export|net\s*meter|solar|buy\s*back", "other"),
    (r"\bf\.?c\.?a\b|\bf\.?p\.?a\b|fuel", "fpa"),
    (r"quarter|\bq\.?t\.?a\b|\bu\.?q\.?a\b", "quarterly_adjustment"),
    (r"meter\s*rent|service\s*rent", "meter_rent"),
    (r"fixed", "fixed"),
    (r"surcharge|\bphl\b|f\.?c\.?\s*sur", "surcharge"),
    (r"variable|cost\s+of\s+electricity|energy|electricity\s+charges|off\s*peak|\bpeak\b|units?\b", "energy"),
]

_TAX_RULES: list[tuple[str, str]] = [
    (r"income\s*tax|\bi\.?t\.?\b|withholding|236", "income_tax"),
    (r"sales\s*tax|g\.?s\.?t|extra\s*tax|further\s*tax", "gst"),
    (r"electricity\s*duty|\be\.?d\.?\b", "electricity_duty"),
    (r"muct|kmc|municipal|toll", "municipal_tax"),
    (r"t\.?v\.?\s*fee|ptv", "other_tax"),
]


def _classify(label: str, hint: str, rules: list[tuple[str, str]], allowed: tuple[str, ...], fallback: str) -> str:
    text = label.lower()
    for pattern, kind in rules:
        if re.search(pattern, text):
            return kind
    hint = (hint or "").strip().lower()
    return hint if hint in allowed else fallback


def classify_charge(label: str, hint: str = "") -> str:
    return _classify(label, hint, _CHARGE_RULES, CHARGE_TYPES, "other")


def classify_tax(label: str, hint: str = "") -> str:
    return _classify(label, hint, _TAX_RULES, TAX_TYPES, "other_tax")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def money(x: float | None) -> float | None:
    return None if x is None else round(float(x), 2)


def normalize_provider(value: str | None) -> str | None:
    if not value:
        return None
    up = value.upper()
    for code, aliases in PROVIDER_ALIASES.items():
        if any(a in up for a in aliases if a != "KE") or up.strip() in ("KE", "K.E"):
            return code
    return value.strip().upper()


def _merge_history(raw: RawExtraction, bill_month: str | None, units_now: float | None) -> tuple[list[HistoryEntry], list[str]]:
    notes: list[str] = []
    by_month: dict[str, HistoryEntry] = {}

    usage = [h for h in raw.usage_history if h.units is not None or h.bill_amount is not None]
    months = [parse_month(h.month) for h in usage]

    # Bar charts (KE) are printed without years on each bar. If the model's months are
    # not a clean consecutive run, rebuild them from the printed order.
    known = [m for m in months if m]
    valid_end = bool(bill_month and known) and max(known) in (bill_month, shift_month(bill_month, -1))  # type: ignore[arg-type]
    needs_rebuild = bool(usage and bill_month) and (
        None in months or not _is_consecutive(months) or not valid_end  # type: ignore[arg-type]
    )
    if needs_rebuild:
        ends_with_current = units_now is not None and usage[-1].units == units_now
        last = bill_month if ends_with_current else shift_month(bill_month, -1)
        months = [shift_month(last, i - len(usage) + 1) for i in range(len(usage))]
        notes.append("Usage-history months were re-derived from their printed order.")

    for h, m in zip(usage, months):
        if not m:
            continue
        by_month[m] = HistoryEntry(month=m, units=h.units, bill_amount=money(h.bill_amount), payment=money(h.payment))

    for p in raw.payment_history:
        m = parse_month(p.month)
        if not m:
            continue
        entry = by_month.setdefault(m, HistoryEntry(month=m))
        if p.bill_amount is not None:
            entry.bill_amount = money(p.bill_amount)
        if p.payment is not None:
            entry.payment = money(p.payment)
        if entry.units is None and p.units is not None:
            entry.units = p.units

    history = sorted(by_month.values(), key=lambda e: e.month)
    if bill_month:
        history = [h for h in history if h.month < bill_month]
    return history, notes


def _is_consecutive(months: list[str]) -> bool:
    if not months:
        return True
    ordered = sorted(set(months))
    if len(ordered) != len(months):
        return False
    return all(shift_month(a, 1) == b for a, b in zip(ordered, ordered[1:]))


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #
def normalize(raw: RawExtraction) -> tuple[Bill, list[str]]:
    notes: list[str] = []
    bill_month = parse_month(raw.bill_month)

    charges: list[LineItem] = []
    for line in raw.charges:
        kind = classify_charge(line.label, line.type)
        amount = money(line.amount) or 0.0
        if kind == "subsidy" and amount > 0:
            amount = -amount  # subsidies always reduce the bill
        charges.append(LineItem(label=line.label.strip(), type=kind, amount=amount))

    taxes = [
        LineItem(label=t.label.strip(), type=classify_tax(t.label, t.type), amount=money(t.amount) or 0.0)
        for t in raw.taxes
    ]

    registers = [MeterRegister(**r.model_dump()) for r in raw.meter_registers]
    units = raw.units_consumed
    if units is None and registers and all(r.units is not None for r in registers):
        units = sum(r.units for r in registers)  # type: ignore[misc]

    single = registers[0] if len(registers) == 1 else None

    tiers = sorted(
        (LateTier(until=parse_date(t.until), surcharge=money(t.surcharge), total_payable=money(t.total_payable) or 0.0)
         for t in raw.late_payment_tiers if t.total_payable),
        key=lambda t: t.total_payable,
    )
    payable = money(raw.payable_within_due_date)
    for t in tiers:
        if t.surcharge is None and payable is not None:
            t.surcharge = money(t.total_payable - payable)

    history, history_notes = _merge_history(raw, bill_month, units)
    notes += history_notes

    export_units = raw.export_units if raw.export_units else None
    if export_units is None:
        exp = [r for r in registers if is_export(r.name)]
        if exp:
            mf = raw.multiplier or 1
            vals = [r.units if r.units is not None else ((r.current - r.previous) * mf if r.current is not None and r.previous is not None else None) for r in exp]
            export_units = sum(v for v in vals if v) or None
    net = NetMetering(
        is_net_metered=bool(export_units) or bool(raw.net_metering_indicated),
        export_units=export_units,
        evidence=(raw.net_metering_evidence or "").strip() or None,
    )

    bill = Bill(
        provider=normalize_provider(raw.provider),
        bill_month=bill_month,
        issue_date=parse_date(raw.issue_date),
        reading_date=parse_date(raw.reading_date),
        due_date=parse_date(raw.due_date),
        tariff=(raw.tariff or "").strip() or None,
        sanctioned_load_kw=raw.sanctioned_load_kw,
        connection_category=(raw.connection_category or "").strip() or None,
        multiplier=raw.multiplier,
        meter_registers=registers,
        units_consumed=units,
        charges=charges,
        taxes=taxes,
        printed_total_charges=money(raw.printed_total_charges),
        printed_total_taxes=money(raw.printed_total_taxes),
        current_bill=money(raw.current_bill),
        arrears=money(raw.arrears),
        other_adjustments=money(raw.other_adjustments),
        fpa_reference_month=parse_month(raw.fpa_reference_month),
        payable_within_due_date=payable,
        payable_after_due_date=tiers[0].total_payable if tiers else None,
        late_payment_tiers=tiers,
        history=history,
        net_metering=net,
    )
    if single and bill.units_consumed is None and single.units is not None:
        bill.units_consumed = single.units
    return bill, notes


def previous_reading(bill: Bill) -> float | None:
    return bill.meter_registers[0].previous if len(bill.meter_registers) == 1 else None


def current_reading(bill: Bill) -> float | None:
    return bill.meter_registers[0].current if len(bill.meter_registers) == 1 else None
