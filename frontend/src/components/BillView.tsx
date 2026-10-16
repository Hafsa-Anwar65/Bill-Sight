import { useState } from "react";
import type { Analysis } from "../types";
import { dayLabel, monthLabel, num, rs } from "../format";
import Reconciliation from "./Reconciliation";
import UsageChart from "./UsageChart";
import LineItems from "./LineItems";
import Checks from "./Checks";
import Answers from "./Answers";
import JsonPanel from "./JsonPanel";
import ChatWidget from "./ChatWidget";
import { Bolt, Calendar, Gauge, Shield, Trend, Wallet } from "./Icons";

const TABS = ["Overview", "Bill lines", "Answers", "Checks", "Data"] as const;
type Tab = (typeof TABS)[number];

const PROVIDER_NAME: Record<string, string> = { KE: "K-Electric", IESCO: "IESCO", LESCO: "LESCO" };

function delta(now: number, before: number): string {
  if (!before) return "—";
  const p = ((now - before) / before) * 100;
  return `${p > 0 ? "+" : ""}${p.toFixed(0)}%`;
}

export default function BillView({ data, image }: { data: Analysis; image?: string }) {
  const { bill, summary: s, checks } = data;
  const [tab, setTab] = useState<Tab>("Overview");
  const units = bill.units_consumed;
  const shown = checks.filter((c) => c.status !== "skip");
  const failed = shown.filter((c) => c.status === "fail").length;
  const tiers = bill.late_payment_tiers;

  const stats = [
    { icon: Bolt, tone: "violet", value: `${num(units)} units`, label: s.units_last_month != null && units != null ? `${delta(units, s.units_last_month)} vs last month` : "used this month" },
    { icon: Gauge, tone: "blue", value: rs(s.average_cost_per_unit, 2), label: "average cost per unit" },
    { icon: Trend, tone: "pink", value: s.units_same_month_last_year != null && units != null ? delta(units, s.units_same_month_last_year) : "—", label: s.units_same_month_last_year != null ? `vs ${num(s.units_same_month_last_year)} units a year ago` : "no data for last year" },
    { icon: Calendar, tone: "amber", value: `~${num(s.forecast_next_month_units)} units`, label: "expected next month" },
  ];

  return (
    <article className="result">
      <section className="summary-row">
        <div className="summary">
          <div className="summary-top">
            <span className="summary-provider">{PROVIDER_NAME[bill.provider ?? ""] ?? bill.provider ?? "Bill"}</span>
            <button className={`verified ${failed ? "bad" : ""}`} onClick={() => setTab("Checks")}>
              <Shield /> {failed ? `${failed} check${failed > 1 ? "s" : ""} failed` : `${shown.length} of ${shown.length} checks passed`}
            </button>
          </div>
          <h2>{monthLabel(bill.bill_month, true)}</h2>
          <div className="summary-main">
            <div>
              <p className="summary-label">Total payable</p>
              <p className="summary-amount">{rs(bill.payable_within_due_date)}</p>
              <p className="summary-due"><Calendar /> Pay by {dayLabel(bill.due_date)}</p>
            </div>
            {tiers.length > 0 && (
              <ul className="summary-late">
                <li className="late-title"><Wallet /> If paid late</li>
                {tiers.map((t, i) => (
                  <li key={i}>
                    <span>{t.until ? `Until ${dayLabel(t.until)}` : i > 0 && tiers[i - 1].until ? `After ${dayLabel(tiers[i - 1].until)}` : "After due date"}</span>
                    <strong>{rs(t.total_payable)}</strong>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <dl className="summary-facts">
            <div><dt>Tariff</dt><dd>{bill.tariff ?? "—"}</dd></div>
            <div><dt>Load</dt><dd>{bill.sanctioned_load_kw != null ? `${num(bill.sanctioned_load_kw, 2)} kW` : "—"}</dd></div>
            <div><dt>Issued</dt><dd>{dayLabel(bill.issue_date)}</dd></div>
            {bill.connection_category && <div><dt>Category</dt><dd>{bill.connection_category}</dd></div>}
          </dl>
        </div>
        {image && (
          <figure className="thumb card">
            <img src={image} alt="The uploaded bill" />
            <figcaption>Your uploaded bill</figcaption>
          </figure>
        )}
      </section>

      <section className="stat-grid" aria-label="Key numbers">
        {stats.map(({ icon: Icon, tone, value, label }) => (
          <div className="stat card" key={label}>
            <span className={`chip-icon ${tone}`}><Icon /></span>
            <p className="stat-value">{value}</p>
            <p className="stat-label">{label}</p>
          </div>
        ))}
      </section>

      <div className="tabs" role="tablist" aria-label="Bill details">
        {TABS.map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}>
            {t}{t === "Answers" ? ` (${data.answers.length})` : ""}
          </button>
        ))}
      </div>

      <div className="tab-body">
        {tab === "Overview" && (
          <>
            <Reconciliation data={data} />
            <UsageChart series={s.series} average={s.average_units_previous_12} />
          </>
        )}
        {tab === "Bill lines" && <LineItems bill={bill} />}
        {tab === "Answers" && <Answers answers={data.answers} />}
        {tab === "Checks" && <Checks checks={checks} attempts={data.attempts} cached={data.cached} />}
        {tab === "Data" && <JsonPanel data={data} />}
      </div>
      <ChatWidget bill={bill} />
    </article>
  );
}
