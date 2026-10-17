"""Deterministic answers to the 12 Level-2 questions.

No language model is involved here: every number is computed with pandas from
the validated `Bill`, and every answer states the months and method it used, so
a reader can check it against the paper bill.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .normalize import month_label, shift_month
from .schema import Answer, Bill

QUESTIONS: list[str] = [
    "Is this a net-metered (solar) connection or a standard connection? How did you tell?",
    "Which month in the last 12 months had the highest units consumed?",
    "How much fuel adjustment am I being charged (shown as FPA or FCA on the bill), and for which month?",
    "If I don't pay on time, what late payment surcharges will be added?",
    "Am I consuming more units than in the same month last year?",
    "What are my average monthly units consumed, and how does this month compare?",
    "How many more units do I consume in summer (June-August) than in winter (December-February)?",
    "Looking at the payments for the 12 months shown on the bill, have I been paying every bill?",
    "Have my units consumed gone up or down over the last 3 months?",
    "Based on the 12 months trend, how many units should I expect to consume next month?",
    "If I wanted to spread my electricity cost evenly across the year, how much should I set aside each month?",
    "If I consume the same units as last month, what would my bill be roughly?",
]


# --------------------------------------------------------------------------- #
# Formatting
# --------------------------------------------------------------------------- #
def rs(x: float) -> str:
    x = round(float(x), 2)
    return f"Rs {x:,.0f}" if x == int(x) else f"Rs {x:,.2f}"


def num(x: float, digits: int = 1) -> str:
    x = round(float(x), digits)
    return f"{x:,.0f}" if x == int(x) else f"{x:,.{digits}f}"


def pct(new: float, old: float) -> str:
    return f"{(new - old) / old * 100:+.1f}%" if old and old > 0 else "n/a"


def pct_paren(new: float, old: float) -> str:
    """' (+12.3%)', or nothing when the base is zero or negative (e.g. solar net-export months)."""
    return f" ({pct(new, old)})" if old and old > 0 else ""


def plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def join_and(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def span(months: list[str]) -> str:
    return month_label(months[0]) if len(months) == 1 else f"{month_label(months[0])} – {month_label(months[-1])}"


def day(iso: str | None) -> str:
    if not iso:
        return ""
    ts = pd.Timestamp(iso)
    return f"{ts.day} {ts:%b %Y}"


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
def month_cost(bill: Bill) -> float:
    """This month's own charges + taxes (no arrears, no late fees)."""
    return round(bill.total_charges + bill.total_taxes, 2)


def usage_frame(bill: Bill) -> pd.DataFrame:
    """History plus the current month, one row per month, oldest first."""
    rows = [h.model_dump() | {"current": False} for h in bill.history]
    if bill.bill_month:
        rows.append({
            "month": bill.bill_month, "units": bill.units_consumed,
            "bill_amount": month_cost(bill) if bill.charges else bill.current_bill,
            "payment": None, "current": True,
        })
    df = pd.DataFrame(rows, columns=["month", "units", "bill_amount", "payment", "current"])
    return df.drop_duplicates("month", keep="last").sort_values("month").reset_index(drop=True)


def _units(df: pd.DataFrame, month: str) -> float | None:
    row = df.loc[df["month"] == month, "units"]
    return None if row.empty or pd.isna(row.iloc[0]) else float(row.iloc[0])


@dataclass
class Facts:
    df: pd.DataFrame
    bill: Bill

    @property
    def known(self) -> pd.DataFrame:
        return self.df.dropna(subset=["units"])

    @property
    def last12(self) -> pd.DataFrame:
        return self.known.tail(12)

    @property
    def previous12(self) -> pd.DataFrame:
        return self.known[~self.known["current"]].tail(12)


# --------------------------------------------------------------------------- #
# Answers
# --------------------------------------------------------------------------- #
def q1_net_metering(f: Facts) -> str:
    b = f.bill
    if b.net_metering.is_net_metered:
        detail = (f"it shows {num(b.net_metering.export_units)} units exported to the grid"
                  if b.net_metering.export_units else (b.net_metering.evidence or "the bill marks it as net-metered"))
        return f"This is a net-metered (solar) connection: {detail.rstrip('.')}."
    regs = b.meter_registers
    if len(regs) > 1:
        reading = f"{len(regs)} import registers ({', '.join(r.name for r in regs)})"
    else:
        reading = "a single import meter reading"
    tariff = f" under the regular tariff {b.tariff}" if b.tariff else ""
    return (f"This is a standard (not net-metered) connection. The bill shows {reading}{tariff}, "
            "with no export units, no export reading and no net-metering credit.")


def q2_peak_month(f: Facts) -> str:
    d = f.last12
    if d.empty:
        return "The bill does not show a usage history."
    top = d["units"].max()
    winners = d.loc[d["units"] == top, "month"].tolist()
    names = " and ".join(month_label(m) for m in winners)
    return (f"{names} had the highest consumption in the last 12 months "
            f"({span(d['month'].tolist())}): {num(top)} units.")


def q3_fpa(f: Facts) -> str:
    b = f.bill
    name = "FCA (fuel charges adjustment)" if b.provider == "KE" else "FPA (fuel price adjustment)"
    amount = b.charges_of("fpa")
    if not amount:
        return f"No {name} is charged on this bill."
    when = (f"It relates to {month_label(b.fpa_reference_month)}"
            if b.fpa_reference_month else "The bill does not say which month it relates to")
    return f"You are charged {rs(amount)} as {name}. {when}."


def q4_late(f: Facts) -> str:
    b = f.bill
    tiers = b.late_payment_tiers
    if not tiers:
        return "The bill does not print any late payment surcharge."
    due = f" (due date {day(b.due_date)})" if b.due_date else ""
    parts, prev_until = [], None
    for t in tiers:
        surcharge = rs(t.surcharge) if t.surcharge is not None else "a surcharge"
        if t.until:
            when = f"until {day(t.until)}"
        elif prev_until:
            when = f"after {day(prev_until)}"
        else:
            when = "after the due date"
        parts.append(f"{surcharge} {when} (total {rs(t.total_payable)})")
        prev_until = t.until or prev_until
    return f"If you pay late{due}, the surcharge is " + "; then ".join(parts) + "."


def q5_yoy(f: Facts) -> str:
    b = f.bill
    if not b.bill_month or b.units_consumed is None:
        return "This month's units are not available."
    ly = shift_month(b.bill_month, -12)
    old = _units(f.df, ly)
    if old is None:
        return f"The bill does not show {month_label(ly)}, so a same-month comparison is not possible."
    now = b.units_consumed
    diff = now - old
    if diff == 0:
        return f"No. You used {num(now)} units, the same as {month_label(ly)}."
    verdict = "Yes" if diff > 0 else "No"
    word = "more" if diff > 0 else "fewer"
    return (f"{verdict}. You used {num(now)} units this month versus {num(old)} units in {month_label(ly)}: "
            f"{num(abs(diff))} {word} units{pct_paren(now, old)}.")


def q6_average(f: Facts) -> str:
    b = f.bill
    d = f.previous12
    if d.empty or b.units_consumed is None:
        return "The bill does not show enough history to work out an average."
    avg = d["units"].mean()
    now = b.units_consumed
    diff = now - avg
    rel = "above" if diff > 0 else "below"
    n = len(d)
    comparison = (f"This month's {num(now)} units is {num(abs(diff))} units"
                  + (f" ({abs(diff / avg * 100):.1f}%)" if avg > 0 else "") + f" {rel} average."
                  if round(diff, 1) else f"This month's {num(now)} units is exactly average.")
    return f"Your average over the previous {n} months ({span(d['month'].tolist())}) is {num(avg)} units per month. {comparison}"


def _season(df: pd.DataFrame, months_of_year: list[int], winter: bool) -> list[str]:
    """Most recent season whose months all appear in the data (falls back to any appearing)."""
    have = set(df["month"])
    years = sorted({int(m[:4]) for m in have}, reverse=True)
    for y in years:
        season = [f"{(y - 1 if winter and mo == 12 else y):04d}-{mo:02d}" for mo in months_of_year]
        if all(m in have for m in season):
            return season
    return []


def q7_seasons(f: Facts) -> str:
    d = f.known
    summer = _season(d, [6, 7, 8], winter=False)
    winter = _season(d, [12, 1, 2], winter=True)
    if not summer or not winter:
        return "The usage history does not cover a full summer (June–August) and a full winter (December–February)."
    s = d[d["month"].isin(summer)]["units"]
    w = d[d["month"].isin(winter)]["units"]
    diff, per_month = s.sum() - w.sum(), s.mean() - w.mean()
    more = "more" if diff >= 0 else "fewer"
    ratio = f" ({s.sum() / w.sum():.1f}× winter)" if w.sum() else ""
    return (f"You use {num(abs(diff))} {more} units in summer than in winter{ratio}. "
            f"Summer ({span(summer)}): {num(s.sum())} units, {num(s.mean())} per month. "
            f"Winter ({span(winter)}): {num(w.sum())} units, {num(w.mean())} per month. "
            f"That is {num(abs(per_month))} units per month {more} in summer.")


def q8_payments(f: Facts) -> str:
    b = f.bill
    d = f.df[(~f.df["current"]) & f.df["bill_amount"].notna()]
    if d.empty:
        return "The bill does not show a payment history."
    months = d["month"].tolist()
    unpaid, partial = [], []
    for _, r in d.iterrows():
        pay = 0.0 if pd.isna(r["payment"]) else float(r["payment"])
        if pay <= 0 and r["bill_amount"] > 0:
            unpaid.append(month_label(r["month"]))
        elif pay < r["bill_amount"] - 1:
            partial.append(f"{month_label(r['month'])} ({rs(pay)} of {rs(r['bill_amount'])})")
    n = len(d)
    scope = f"the {plural(n, 'month')} shown ({span(months)})"
    arrears = (f" The bill carries arrears of {rs(b.arrears)} into this month."
               if b.arrears and b.arrears > 1 else "")
    if not unpaid and not partial:
        return f"Yes. Every bill in {scope} was paid in full.{arrears}"
    bits = []
    if unpaid:
        bits.append(f"no payment is recorded for {join_and(unpaid)}")
    if partial:
        bits.append(f"only part was paid for {join_and(partial)}")
    missed = len(unpaid) + len(partial)
    return f"No. Across {scope}, {' and '.join(bits)} ({missed} of {n} months).{arrears}"


def q9_trend(f: Facts) -> str:
    d = f.known.tail(3)
    if len(d) < 2:
        return "The bill does not show enough months to see a trend."
    units, months = d["units"].tolist(), d["month"].tolist()
    path = " → ".join(f"{num(u)} ({month_label(m)})" for u, m in zip(units, months))
    change = units[-1] - units[0]
    steps = [b - a for a, b in zip(units, units[1:])]
    if all(s < 0 for s in steps):
        verdict = "Down"
    elif all(s > 0 for s in steps):
        verdict = "Up"
    elif change == 0:
        verdict = "Flat overall"
    else:
        verdict = f"Mixed, {'up' if change > 0 else 'down'} overall"
    return (f"{verdict}. Units went {path}: {'+' if change > 0 else ''}{num(change)} units"
            f"{pct_paren(units[-1], units[0])} across the {len(units)} months.")


def forecast_next(f: Facts) -> tuple[float | None, str]:
    b = f.bill
    if not b.bill_month or b.units_consumed is None:
        return None, "This month's units are not available."
    nxt = shift_month(b.bill_month, 1)
    ly_next = _units(f.df, shift_month(nxt, -12))
    ly_now = _units(f.df, shift_month(b.bill_month, -12))
    if ly_next is not None and ly_now and ly_now > 0 and ly_next > 0:
        ratio = min(max(b.units_consumed / ly_now, 0.5), 2.0)
        est = round(ly_next * ratio)
        how = (f"{month_label(shift_month(nxt, -12))} used {num(ly_next)} units, and this month is "
               f"{pct(b.units_consumed, ly_now)} versus the same month last year "
               f"({num(b.units_consumed)} vs {num(ly_now)}), so {num(ly_next)} × {ratio:.3f} ≈ {est}")
        return est, f"About {est} units in {month_label(nxt)}. Method: {how}."
    if ly_next is not None:
        return ly_next, f"About {num(ly_next)} units in {month_label(nxt)}, the same as {month_label(shift_month(nxt, -12))}."
    recent = f.known.tail(3)
    est = round(recent["units"].mean())
    return est, f"About {est} units in {month_label(nxt)}, the average of the last {len(recent)} months."


def q10_forecast(f: Facts) -> str:
    return forecast_next(f)[1]


def q11_budget(f: Facts) -> str:
    b = f.bill
    d = f.last12.copy()
    if d.empty or not b.units_consumed:
        return "The bill does not show enough history to plan a monthly budget."
    rate = max(month_cost(b), 0) / b.units_consumed
    actual = d["bill_amount"].notna()
    d.loc[~actual, "bill_amount"] = d.loc[~actual, "units"] * rate
    total = d["bill_amount"].sum()
    monthly = total / len(d)
    if monthly <= 0:
        return (f"You don't need to set anything aside on average. Over {span(d['month'].tolist())} your credits "
                f"(for example from solar export) covered your charges, a net of {rs(round(-total))} in your favour.")
    n_act, n_est = int(actual.sum()), int((~actual).sum())
    if n_est:
        basis = (f"{n_act} months use the billed amounts printed on the bill and {n_est} months are estimated "
                 f"from their units at this bill's average of {rs(round(rate, 2))} per unit")
    else:
        basis = "all from the billed amounts printed on the bill"
    return (f"Set aside about {rs(round(monthly))} per month. Your electricity cost over "
            f"{span(d['month'].tolist())} comes to about {rs(round(total))} ({basis}), "
            f"divided by {len(d)} months.")


def q12_same_as_last(f: Facts) -> str:
    b = f.bill
    if not b.history or b.units_consumed in (None, 0):
        return "The bill does not show last month's units."
    last = b.history[-1]
    if last.units is None:
        return "The bill does not show last month's units."
    fixed = b.charges_of("fixed")
    cost = month_cost(b)
    est = fixed + (cost - fixed) * last.units / b.units_consumed  # type: ignore[operator]
    if est <= 0:
        return (f"About nothing to pay: at {num(last.units)} units (the same as {month_label(last.month)}), this month's "
                "credits would still cover the charges, so the bill would roughly come to zero.")
    fixed_txt = f", keeping the fixed charge of {rs(fixed)}" if fixed else ""
    actual = (f" For reference, your actual bill for {month_label(last.month)} was {rs(last.bill_amount)}."
              if last.bill_amount else "")
    return (f"Roughly {rs(round(est))} for {num(last.units)} units (the same as {month_label(last.month)}). "
            f"This scales this month's charges and taxes ({rs(cost)} for {num(b.units_consumed)} units) "
            f"by units used{fixed_txt}; "
            f"a different tariff slab or fuel adjustment can change it.{actual}")


HANDLERS = [q1_net_metering, q2_peak_month, q3_fpa, q4_late, q5_yoy, q6_average,
            q7_seasons, q8_payments, q9_trend, q10_forecast, q11_budget, q12_same_as_last]


def answer_all(bill: Bill) -> list[Answer]:
    facts = Facts(usage_frame(bill), bill)
    out = []
    for i, (q, fn) in enumerate(zip(QUESTIONS, HANDLERS), start=1):
        try:
            text = fn(facts)
        except Exception:  # noqa: BLE001 - one bad field must not sink the other answers
            text = "This could not be worked out from the data on this bill."
        out.append(Answer(id=f"Q{i}", question=q, answer=text))
    return out


def summary(bill: Bill) -> dict:
    """Headline numbers for the dashboard and for grounding free-form questions."""
    facts = Facts(usage_frame(bill), bill)
    cost = month_cost(bill)
    prev = bill.history[-1] if bill.history else None
    ly = _units(facts.df, shift_month(bill.bill_month, -12)) if bill.bill_month else None
    by_type: dict[str, float] = {}
    for c in bill.charges + bill.taxes:
        by_type[c.type] = round(by_type.get(c.type, 0) + c.amount, 2)
    est, _ = forecast_next(facts)
    return {
        "month_cost": cost,
        "average_cost_per_unit": round(cost / bill.units_consumed, 2) if bill.units_consumed and cost > 0 else None,
        "tax_share_percent": round(bill.total_taxes / cost * 100, 1) if cost > 0 else None,
        "total_charges": bill.total_charges,
        "total_taxes": bill.total_taxes,
        "units_last_month": prev.units if prev else None,
        "units_same_month_last_year": ly,
        "average_units_previous_12": round(facts.previous12["units"].mean(), 1) if not facts.previous12.empty else None,
        "forecast_next_month_units": est,
        "late_fee_if_paid_late": bill.late_payment_tiers[0].surcharge if bill.late_payment_tiers else None,
        "amount_by_type": by_type,
        "series": [
            {"month": r.month, "units": None if pd.isna(r.units) else float(r.units),
             "bill_amount": None if pd.isna(r.bill_amount) else float(r.bill_amount), "current": bool(r.current)}
            for r in facts.df.itertuples()
        ],
    }


# --------------------------------------------------------------------------- #
# Insights: short, factual tips shown on the dashboard
# --------------------------------------------------------------------------- #
def _tou_rates(bill: Bill) -> tuple[float, float, float, float] | None:
    """(peak units, peak rate, off-peak units, off-peak rate) for time-of-use bills."""
    regs = {r.name.lower(): r.units for r in bill.meter_registers if r.units}
    peak_units = next((u for n, u in regs.items() if "peak" in n and "off" not in n), None)
    off_units = next((u for n, u in regs.items() if "off" in n), None)
    energy = [c for c in bill.charges if c.type == "energy"]
    peak_amt = sum(c.amount for c in energy if "peak" in c.label.lower() and "off" not in c.label.lower())
    off_amt = sum(c.amount for c in energy if "off" in c.label.lower())
    if not (peak_units and off_units and peak_amt and off_amt):
        return None
    return peak_units, peak_amt / peak_units, off_units, off_amt / off_units


def insights(bill: Bill) -> list[dict[str, str]]:
    f = Facts(usage_frame(bill), bill)
    out: list[dict[str, str]] = []

    def add(kind: str, title: str, detail: str) -> None:
        out.append({"kind": kind, "title": title, "detail": detail})

    tiers = bill.late_payment_tiers
    if tiers and tiers[0].surcharge:
        add("save", f"Pay by {day(bill.due_date)} to save {rs(tiers[0].surcharge)}",
            f"Paying late raises the bill to {rs(tiers[0].total_payable)}"
            + (f", and to {rs(tiers[-1].total_payable)} later." if len(tiers) > 1 else "."))

    tou = _tou_rates(bill)
    if tou:
        pu, pr, ou, orate = tou
        saving = 0.1 * pu * (pr - orate)
        if saving > 0:
            add("save", f"Peak units cost {rs(round(pr, 2))} vs {rs(round(orate, 2))} off-peak",
                f"You used {num(pu)} units in peak hours. Moving 10% of them to off-peak hours saves about {rs(round(saving))} a month.")

    if bill.arrears and bill.arrears > 1:
        add("warn", f"{rs(bill.arrears)} carried over from earlier bills",
            "This amount is unpaid from previous months and is included in the payable total.")
    elif bill.arrears and bill.arrears < -1:
        add("good", f"You have a credit of {rs(-bill.arrears)}", "It has been deducted from this bill.")

    if bill.history and bill.units_consumed is not None:
        last = bill.history[-1]
        if last.units:
            change = (bill.units_consumed - last.units) / last.units * 100
            if abs(change) >= 15:
                add("good" if change < 0 else "warn",
                    f"Usage {'down' if change < 0 else 'up'} {abs(change):.0f}% from last month",
                    f"{num(bill.units_consumed)} units this month vs {num(last.units)} in {month_label(last.month)}.")

    prev = f.previous12
    if not prev.empty and bill.units_consumed is not None:
        avg = prev["units"].mean()
        if avg and bill.units_consumed > avg * 1.2:
            add("warn", "Above your usual usage",
                f"This month is {num(bill.units_consumed)} units, {((bill.units_consumed / avg) - 1) * 100:.0f}% above your 12-month average of {num(avg)}.")

    subsidy = -bill.charges_of("subsidy")
    if subsidy > 0:
        add("good", f"Government subsidy saved you {rs(subsidy)}", "It is already deducted from your electricity charges.")

    fpa = bill.charges_of("fpa")
    if fpa > 0:
        when = f" for {month_label(bill.fpa_reference_month)}" if bill.fpa_reference_month else ""
        add("info", f"Fuel adjustment adds {rs(fpa)}", f"A charge for past fuel costs{when}, not for this month's usage.")

    if bill.payable_within_due_date is not None and bill.payable_within_due_date <= 0:
        add("good", "Nothing to pay this month",
            "Your earlier credit is larger than this month's charges, so the balance carries forward.")

    cost = month_cost(bill)
    if cost > 0 and bill.total_taxes:
        add("info", f"Taxes are {bill.total_taxes / cost * 100:.0f}% of this month's charges",
            f"{rs(bill.total_taxes)} of {rs(cost)} goes to taxes and duties.")

    est, _ = forecast_next(f)
    if est is not None and bill.bill_month:
        add("info", f"Expect about {num(est)} units in {month_label(shift_month(bill.bill_month, 1))}",
            "Based on the same month last year, adjusted for how this year compares.")
    return out
