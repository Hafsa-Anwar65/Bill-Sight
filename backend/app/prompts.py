"""Prompts. Bump PROMPT_VERSION whenever a prompt changes so the cache refreshes."""

PROMPT_VERSION = "v3"

EXTRACTION_PROMPT = """
You are reading a Pakistani electricity bill (K-Electric, IESCO, LESCO or another DISCO).
Copy numbers EXACTLY as printed. Never calculate, guess or round a value that is not printed.
If a field is not printed, return null (or an empty list). Return JSON only.

IGNORE: handwritten notes, pen marks, stamps, bank stamps, circled numbers, and anything
redacted. IGNORE all personal data: names, addresses, CNIC, reference/consumer/account/meter numbers.

FIELDS
- provider: "KE" for K-Electric, otherwise the company code (IESCO, LESCO, GEPCO, ...).
- bill_month: the billing month as YYYY-MM ("Apr-2026" -> "2026-04", "SEP 26" -> "2026-09").
- issue_date, reading_date, due_date: YYYY-MM-DD.
- tariff (e.g. "A1-R", "A-1A(01)"), sanctioned_load_kw (San/Sanc Load), connection_category
  ("Protected"/"Unprotected" if printed), multiplier (MF, IESCO/LESCO only).
- meter_registers: one entry per printed reading row with previous, current and units.
  K-Electric time-of-use bills have two rows ("Off Peak", "Peak"); most bills have one ("Energy").
- units_consumed: total units billed this month.

CHARGES (electricity charges, before taxes). One entry per printed line, label exactly as printed.
  type codes: energy | fixed | fpa | quarterly_adjustment | surcharge | meter_rent | subsidy | other
  * K-Electric: take every line in "Bill Calculation" ABOVE "Electricity Charges":
    Fixed Charges -> fixed; Variable ... (Off Peak / Peak / Upto N Units) -> energy;
    Uniform Quarterly Adjustment (may appear twice, may be negative) -> quarterly_adjustment;
    FCA -> fpa; Additional Surcharge (PHL) -> surcharge.
    printed_total_charges = the "Electricity Charges" total.
  * IESCO/LESCO summary layout: "Total Electricity Charges" -> energy; "Subsidies" -> subsidy;
    "Total FPA" -> fpa. Skip any line whose amount is 0.
    Do NOT add "Net Electricity Charges", "Current Bill", "Grand Total" or "Arrears" as charges.
    printed_total_charges = null for this layout.
  * Detailed layout (COST OF ELECTRICITY, FUEL PRICE ADJUSTMENT, F.C SURCHARGE, QTR TARIFF ADJ,
    FIXED CHARGES, METER RENT ...): one entry per non-zero line.

TAXES. One entry per printed non-zero tax line, label exactly as printed.
  type codes: gst | electricity_duty | income_tax | municipal_tax | other_tax
  * K-Electric: Electricity Duty -> electricity_duty; Sales Tax -> gst; MUCT (KMC) -> municipal_tax;
    Income Tax -> income_tax. printed_total_taxes = the "Taxes and Duties" total.
  * IESCO/LESCO summary layout prints one line "Taxes" -> type other_tax. printed_total_taxes = null.
  * Detailed layout: GST, GST ON FPA -> gst; ELECTRICITY DUTY, ED ON FPA -> electricity_duty;
    INCOME TAX -> income_tax; TV FEE -> other_tax.

TOTALS
- current_bill: K-Electric "Electricity Charges for current month" / "Current Bill Amount";
  IESCO/LESCO "Current Bill".
- arrears: K-Electric "Previous Dues"/"Remaining Dues" (keep the sign, e.g. -0.47); IESCO/LESCO "Arrears".
- other_adjustments: sum of printed Installment + Adjustments + credits (null if all are 0 or blank).
- fpa_reference_month: the month the fuel adjustment relates to, as YYYY-MM ("FCA :Jul-26" -> "2026-07";
  on IESCO/LESCO it is stated in the yellow FPA note, e.g. "Jul 26 ... FPA").
- payable_within_due_date: "Amount Payable within Due Date" / "Payable Within Due Date" / "Grand Total".
- late_payment_tiers: every printed after-due-date amount, in time order. For each: until (last date
  of that tier, YYYY-MM-DD, or null for the final open-ended tier), surcharge (the printed L.P./LPS
  surcharge amount for that tier), total_payable.
  K-Electric: 5% LPS tier then 10% LPS tier. IESCO/LESCO: "Till <date>" then "After <date>".

HISTORY
- usage_history: every month in the usage history / bill history (13-month bar chart on K-Electric,
  table on IESCO/LESCO), oldest first, including the current month if it is shown.
  month as YYYY-MM (work out the year from the 2025/2026 headings or the table), units, and for
  tables also bill_amount and payment.
- payment_history: K-Electric "Billing & Payment History" rows: month (YYYY-MM from MM/YY),
  bill_amount (Billed Amount), payment.

NET METERING
- export_units: units exported to the grid if printed (net-metering / solar bills), else null.
- net_metering_indicated: true only if the bill prints net metering, export/import readings or a
  solar/net-metering tariff. Otherwise false.
- net_metering_evidence: one short sentence on what you saw that decided it.
""".strip()

RETRY_PROMPT = """
Your previous reading of this bill failed these consistency checks:
{failures}

Look at the bill again and re-read the fields involved, digit by digit. Common causes: a missed
or extra charge line, a sign error on an adjustment, a misread digit, or a total copied from the
wrong box. Return the complete corrected JSON.
""".strip()

ASK_PROMPT = """
You answer questions about one electricity bill for a Pakistani household.
Use ONLY the BILL and FACTS below. Every number you state must appear in them.
If the answer is not in the data, say so plainly. Be brief: 1-3 sentences, amounts as "Rs 1,234".
Reply in the language of the question (English, Urdu or Roman Urdu).

BILL:
{bill}

FACTS (already calculated, trust these):
{facts}

QUESTION: {question}
""".strip()
