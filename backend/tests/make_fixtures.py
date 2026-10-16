"""Ground truth for the sample bills, transcribed by hand from the images.

Each fixture is exactly what a perfect vision read should return (RawExtraction).
Run: python tests/make_fixtures.py
"""
import json
from pathlib import Path

OUT = Path(__file__).parent / "fixtures"


def months(start_y, start_m, n):
    out = []
    y, m = start_y, start_m
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def usage(start, units, amounts=None, payments=None):
    ms = months(*start, len(units))
    rows = []
    for i, (mo, u) in enumerate(zip(ms, units)):
        r = {"month": mo, "units": u}
        if amounts:
            r["bill_amount"], r["payment"] = amounts[i], payments[i]
        rows.append(r)
    return rows


def line(label, type_, amount):
    return {"label": label, "type": type_, "amount": amount}


FIXTURES = {
    "ke_2026-04_286": {
        "provider": "K-Electric", "bill_month": "2026-04", "issue_date": "2026-04-06",
        "reading_date": "2026-04-01", "due_date": "2026-04-20", "tariff": "A1-R",
        "sanctioned_load_kw": 8, "meter_registers": [
            {"name": "Off Peak", "previous": 36, "current": 274, "units": 238},
            {"name": "Peak", "previous": 8, "current": 56, "units": 48}],
        "units_consumed": 286,
        "charges": [line("Fixed Charges", "fixed", 2700.00), line("Variable Off Peak", "energy", 8218.14),
                    line("Variable Peak", "energy", 2248.80), line("Uniform Quarterly Adjustment", "quarterly_adjustment", 100.22),
                    line("FCA :Feb-26", "fpa", 290.39), line("Additional Surcharge (PHL)", "surcharge", 923.78)],
        "taxes": [line("Electricity Duty", "electricity_duty", 176.72), line("Sales Tax u/s 3(1)*", "gst", 2638.45)],
        "printed_total_charges": 14481.33, "printed_total_taxes": 2815.17,
        "current_bill": 17296.50, "arrears": -0.47, "fpa_reference_month": "2026-02",
        "payable_within_due_date": 17297,
        "late_payment_tiers": [{"until": "2026-04-23", "surcharge": 724.07, "total_payable": 18022},
                               {"until": None, "surcharge": 1448.13, "total_payable": 18745}],
        "usage_history": usage((2025, 4), [214, 255, 438, 306, 249, 274, 277, 264, 227, 169, 204, 185, 286]),
        "payment_history": [{"month": "2026-03", "bill_amount": 12136.42, "payment": 12136},
                            {"month": "2026-02", "bill_amount": 12294.67, "payment": 12295},
                            {"month": "2026-01", "bill_amount": 10059.17, "payment": 10059}],
        "net_metering_indicated": False,
    },
    "ke_2026-09_159": {
        "provider": "K-Electric", "bill_month": "2026-09", "issue_date": "2026-09-08",
        "reading_date": "2026-09-04", "due_date": "2026-09-22", "tariff": "A1-R", "sanctioned_load_kw": 3,
        "meter_registers": [{"name": "Energy", "previous": 9935, "current": 10094, "units": 159}],
        "units_consumed": 159,
        "charges": [line("Fixed Charges", "fixed", 900.00), line("Variable Upto 200 Units (Unprotected)", "energy", 4596.69),
                    line("Uniform Quarterly Adjustment", "quarterly_adjustment", -274.99),
                    line("Uniform Quarterly Adjustment", "quarterly_adjustment", 10.66),
                    line("FCA :Jul-26", "fpa", 613.31), line("Additional Surcharge (PHL)", "surcharge", 513.57)],
        "taxes": [line("Electricity Duty", "electricity_duty", 81.89), line("Sales Tax u/s 3(1)*", "gst", 1159.40),
                  line("MUCT (KMC)", "municipal_tax", 20.00)],
        "printed_total_charges": 6359.24, "printed_total_taxes": 1261.29,
        "current_bill": 7620.53, "arrears": -0.41, "fpa_reference_month": "2026-07",
        "payable_within_due_date": 7621,
        "late_payment_tiers": [{"until": "2026-09-25", "surcharge": 317.96, "total_payable": 7939},
                               {"until": None, "surcharge": 635.92, "total_payable": 8257}],
        "usage_history": usage((2025, 9), [176, 173, 187, 124, 96, 88, 115, 151, 171, 261, 298, 235, 159]),
        "payment_history": [{"month": "2026-08", "bill_amount": 11180.07, "payment": 11180},
                            {"month": "2026-07", "bill_amount": 13605.87, "payment": 13606},
                            {"month": "2026-06", "bill_amount": 12866.40, "payment": 12866}],
        "net_metering_indicated": False,
    },
    "ke_2026-09_459": {
        "provider": "K-Electric", "bill_month": "2026-09", "issue_date": "2026-09-10",
        "reading_date": "2026-09-07", "due_date": "2026-09-24", "tariff": "A1-R", "sanctioned_load_kw": 2,
        "meter_registers": [{"name": "Energy", "previous": 16538, "current": 16997, "units": 459}],
        "units_consumed": 459,
        "charges": [line("Fixed Charges", "fixed", 1000.00), line("Variable Upto 500 Units", "energy", 17878.05),
                    line("Uniform Quarterly Adjustment", "quarterly_adjustment", -705.63),
                    line("Uniform Quarterly Adjustment", "quarterly_adjustment", 53.83),
                    line("FCA :Jul-26", "fpa", 1280.14), line("Additional Surcharge (PHL)", "surcharge", 1482.57)],
        "taxes": [line("Electricity Duty", "electricity_duty", 299.83), line("Sales Tax u/s 3(1)*", "gst", 3831.98),
                  line("MUCT (KMC)", "municipal_tax", 125.00)],
        "printed_total_charges": 20988.96, "printed_total_taxes": 4256.81,
        "current_bill": 25245.77, "arrears": -0.20, "fpa_reference_month": "2026-07",
        "payable_within_due_date": 25246,
        "late_payment_tiers": [{"until": "2026-09-27", "surcharge": 1049.45, "total_payable": 26296},
                               {"until": None, "surcharge": 2098.90, "total_payable": 27345}],
        "usage_history": usage((2025, 9), [374, 368, 277, 179, 151, 141, 221, 269, 286, 563, 622, 576, 459]),
        "payment_history": [{"month": "2026-08", "bill_amount": 30854.13, "payment": 30854},
                            {"month": "2026-07", "bill_amount": 33987.16, "payment": 33987},
                            {"month": "2026-06", "bill_amount": 31254.95, "payment": 31255}],
        "net_metering_indicated": False,
    },
    "iesco_2026-09_177": {
        "provider": "IESCO", "bill_month": "2026-09", "issue_date": "2026-09-14", "reading_date": "2026-09-13",
        "due_date": "2026-09-24", "tariff": "A-1A(01)", "sanctioned_load_kw": 4, "connection_category": "Unprotected",
        "multiplier": 1, "meter_registers": [{"name": "Energy", "previous": 3624.46, "current": 3801.12, "units": 177}],
        "units_consumed": 177,
        "charges": [line("Total Electricity Charges", "energy", 7711), line("Subsidies", "subsidy", 1002),
                    line("Total FPA", "fpa", 599)],
        "taxes": [line("Taxes", "other_tax", 1295)],
        "current_bill": 8004, "arrears": 0, "fpa_reference_month": "2026-07", "payable_within_due_date": 8603,
        "late_payment_tiers": [{"until": "2026-09-28", "surcharge": 336, "total_payable": 8939},
                               {"until": None, "surcharge": 671, "total_payable": 9274}],
        "usage_history": usage((2025, 9), [172, 152, 113, 139, 95, 166, 119, 128, 122, 188, 243, 246],
                               [2083, 1822, 1374, 1965, 1285, 2572, 3268, 3516, 3134, 7601, 11684, 11926],
                               [2083, 1822, 1374, 1965, 1285, 2572, 3268, 3516, 0, 7601, 11684, 11926]),
        "net_metering_indicated": False,
    },
    "iesco_2026-09_58": {
        "provider": "IESCO", "bill_month": "2026-09", "issue_date": "2026-09-28", "reading_date": "2026-09-27",
        "due_date": "2026-10-12", "tariff": "A-1A(01)", "sanctioned_load_kw": 3, "connection_category": "Protected",
        "multiplier": 1, "meter_registers": [{"name": "Energy", "previous": 1156.14, "current": 1213.9, "units": 58}],
        "units_consumed": 58,
        "charges": [line("Total Electricity Charges", "energy", 2636), line("Subsidies", "subsidy", 1393),
                    line("Total FPA", "fpa", 172)],
        "taxes": [line("Taxes", "other_tax", 234)],
        "current_bill": 1477, "arrears": 0, "fpa_reference_month": "2026-07", "payable_within_due_date": 1649,
        "late_payment_tiers": [{"until": "2026-10-15", "surcharge": 62, "total_payable": 1711},
                               {"until": None, "surcharge": 124, "total_payable": 1773}],
        "usage_history": usage((2025, 9), [75, 46, 30, 40, 50, 27, 8, 23, 24, 48, 70, 49],
                               [816, 506, 385, 539, 676, 744, 914, 1066, 1034, 1271, 1470, 1277],
                               [850, 548, 385, 539, 732, 775, 914, 1066, 1034, 1271, 1470, 1277]),
        "net_metering_indicated": False,
    },
    "iesco_2026-08_676": {
        "provider": "IESCO", "bill_month": "2026-08", "issue_date": "2026-08-09", "reading_date": "2026-08-08",
        "due_date": "2026-08-24", "tariff": "A-1a(01)", "sanctioned_load_kw": 1.0, "connection_category": "Unprotected",
        "multiplier": 1, "meter_registers": [{"name": "Energy", "previous": 5949.08, "current": 6625.57, "units": 676}],
        "units_consumed": 676,
        "charges": [line("Total Electricity Charges", "energy", 29807), line("Total FPA", "fpa", 370.76)],
        "taxes": [line("Taxes", "other_tax", 8516)],
        "current_bill": 38323, "arrears": 31203, "fpa_reference_month": "2026-06", "payable_within_due_date": 69897,
        "late_payment_tiers": [{"until": "2026-08-27", "surcharge": 1491, "total_payable": 71388},
                               {"until": None, "surcharge": 2981, "total_payable": 72878}],
        "usage_history": usage((2025, 8), [721, 597, 656, 182, 143, 155, 175, 142, 154, 267, 412, 525],
                               [80594, 32414, 73264, 6395, 4767, 5816, 6844, 13546, 20670, 12125, 34613, 28959],
                               [80594, 0, 73264, 6395, 4767, 5816, 0, 0, 20670, 0, 34613, 0]),
        "net_metering_indicated": False,
    },
}

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, data in FIXTURES.items():
        (OUT / f"{name}.json").write_text(json.dumps(data, indent=2))
    print(f"wrote {len(FIXTURES)} fixtures")
