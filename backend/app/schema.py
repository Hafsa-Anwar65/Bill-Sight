"""Data models.

`RawExtraction` is what the vision model is asked to return (loose types, so the
model never fails schema validation). `Bill` is the clean, normalized record
every other module works with.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

ChargeType = Literal[
    "energy", "fixed", "fpa", "quarterly_adjustment", "surcharge", "meter_rent", "subsidy", "other"
]
TaxType = Literal["gst", "electricity_duty", "income_tax", "municipal_tax", "other_tax"]

CHARGE_TYPES: tuple[str, ...] = ChargeType.__args__  # type: ignore[attr-defined]
TAX_TYPES: tuple[str, ...] = TaxType.__args__  # type: ignore[attr-defined]


# --------------------------------------------------------------------------- #
# What the model returns
# --------------------------------------------------------------------------- #
class RawLine(BaseModel):
    label: str = Field(description="Line name exactly as printed on the bill")
    type: str = Field(description="One of the allowed type codes")
    amount: float = Field(description="Amount in rupees exactly as printed (negative if printed negative)")


class RawRegister(BaseModel):
    name: str = Field(description="e.g. 'Energy', 'Off Peak', 'Peak'")
    previous: Optional[float] = None
    current: Optional[float] = None
    units: Optional[float] = None


class RawHistory(BaseModel):
    month: str = Field(description="YYYY-MM")
    units: Optional[float] = None
    bill_amount: Optional[float] = None
    payment: Optional[float] = None


class RawLateTier(BaseModel):
    until: Optional[str] = Field(None, description="Last date of this tier as YYYY-MM-DD, null if open-ended")
    surcharge: Optional[float] = None
    total_payable: float


class RawExtraction(BaseModel):
    provider: Optional[str] = None
    bill_month: Optional[str] = None
    issue_date: Optional[str] = None
    reading_date: Optional[str] = None
    due_date: Optional[str] = None
    tariff: Optional[str] = None
    sanctioned_load_kw: Optional[float] = None
    connection_category: Optional[str] = None
    multiplier: Optional[float] = None
    meter_registers: list[RawRegister] = []
    units_consumed: Optional[float] = None
    charges: list[RawLine] = []
    taxes: list[RawLine] = []
    printed_total_charges: Optional[float] = None
    printed_total_taxes: Optional[float] = None
    current_bill: Optional[float] = None
    arrears: Optional[float] = None
    other_adjustments: Optional[float] = None
    fpa_reference_month: Optional[str] = None
    payable_within_due_date: Optional[float] = None
    late_payment_tiers: list[RawLateTier] = []
    usage_history: list[RawHistory] = []
    payment_history: list[RawHistory] = []
    export_units: Optional[float] = None
    net_metering_indicated: Optional[bool] = None
    net_metering_evidence: Optional[str] = None


# --------------------------------------------------------------------------- #
# Clean record
# --------------------------------------------------------------------------- #
class LineItem(BaseModel):
    label: str
    type: str
    amount: float


class MeterRegister(BaseModel):
    name: str
    previous: Optional[float] = None
    current: Optional[float] = None
    units: Optional[float] = None


class HistoryEntry(BaseModel):
    month: str
    units: Optional[float] = None
    bill_amount: Optional[float] = None
    payment: Optional[float] = None


class LateTier(BaseModel):
    until: Optional[str] = None
    surcharge: Optional[float] = None
    total_payable: float


class NetMetering(BaseModel):
    is_net_metered: bool = False
    export_units: Optional[float] = None
    evidence: Optional[str] = None


class Bill(BaseModel):
    provider: Optional[str] = None
    bill_month: Optional[str] = None
    issue_date: Optional[str] = None
    reading_date: Optional[str] = None
    due_date: Optional[str] = None
    tariff: Optional[str] = None
    sanctioned_load_kw: Optional[float] = None
    connection_category: Optional[str] = None
    multiplier: Optional[float] = None
    meter_registers: list[MeterRegister] = []
    units_consumed: Optional[float] = None
    charges: list[LineItem] = []
    taxes: list[LineItem] = []
    printed_total_charges: Optional[float] = None
    printed_total_taxes: Optional[float] = None
    current_bill: Optional[float] = None
    arrears: Optional[float] = None
    other_adjustments: Optional[float] = None
    fpa_reference_month: Optional[str] = None
    payable_within_due_date: Optional[float] = None
    payable_after_due_date: Optional[float] = None
    late_payment_tiers: list[LateTier] = []
    history: list[HistoryEntry] = Field(
        default_factory=list, description="Months BEFORE bill_month, oldest first"
    )
    net_metering: NetMetering = Field(default_factory=NetMetering)

    # Convenience totals -------------------------------------------------- #
    @property
    def total_charges(self) -> float:
        return round(sum(c.amount for c in self.charges), 2)

    @property
    def total_taxes(self) -> float:
        return round(sum(t.amount for t in self.taxes), 2)

    def charges_of(self, kind: str) -> float:
        return round(sum(c.amount for c in self.charges if c.type == kind), 2)


class Check(BaseModel):
    id: str
    label: str
    status: Literal["pass", "warn", "fail", "skip"]
    detail: str
    critical: bool = False


class Answer(BaseModel):
    id: str
    question: str
    answer: str
    evidence: list[str] = []
