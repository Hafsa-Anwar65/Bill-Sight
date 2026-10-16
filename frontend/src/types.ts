export interface LineItem { label: string; type: string; amount: number }
export interface MeterRegister { name: string; previous: number | null; current: number | null; units: number | null }
export interface HistoryEntry { month: string; units: number | null; bill_amount: number | null; payment: number | null }
export interface LateTier { until: string | null; surcharge: number | null; total_payable: number }

export interface Bill {
  provider: string | null;
  bill_month: string | null;
  issue_date: string | null;
  reading_date: string | null;
  due_date: string | null;
  tariff: string | null;
  sanctioned_load_kw: number | null;
  connection_category: string | null;
  multiplier: number | null;
  meter_registers: MeterRegister[];
  units_consumed: number | null;
  charges: LineItem[];
  taxes: LineItem[];
  printed_total_charges: number | null;
  printed_total_taxes: number | null;
  current_bill: number | null;
  arrears: number | null;
  other_adjustments: number | null;
  fpa_reference_month: string | null;
  payable_within_due_date: number | null;
  payable_after_due_date: number | null;
  late_payment_tiers: LateTier[];
  history: HistoryEntry[];
  net_metering: { is_net_metered: boolean; export_units: number | null; evidence: string | null };
}

export interface Check {
  id: string;
  label: string;
  status: "pass" | "warn" | "fail" | "skip";
  detail: string;
  critical: boolean;
}

export interface Answer { id: string; question: string; answer: string }

export interface SeriesPoint { month: string; units: number | null; bill_amount: number | null; current: boolean }

export interface Summary {
  month_cost: number;
  average_cost_per_unit: number | null;
  tax_share_percent: number | null;
  total_charges: number;
  total_taxes: number;
  units_last_month: number | null;
  units_same_month_last_year: number | null;
  average_units_previous_12: number | null;
  forecast_next_month_units: number | null;
  late_fee_if_paid_late: number | null;
  amount_by_type: Record<string, number>;
  series: SeriesPoint[];
}

export interface Analysis {
  bill_id: string;
  image_hash: string;
  attempts: number;
  cached: boolean;
  notes: string[];
  bill: Bill;
  level1: Record<string, unknown>;
  checks: Check[];
  answers: Answer[];
  summary: Summary;
}

export interface Health { ok: boolean; model: string; api_key_set: boolean }
