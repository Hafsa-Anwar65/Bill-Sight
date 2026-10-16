import { useEffect, useState } from "react";
import type { Analysis } from "../types";
import { dayLabel, download, monthLabel, num, rs } from "../format";
import { dueDateIcs } from "../reminder";
import { toast } from "../toast";
import Reconciliation from "./Reconciliation";
import UsageChart from "./UsageChart";
import LineItems from "./LineItems";
import Checks from "./Checks";
import Answers from "./Answers";
import Insights from "./Insights";
import JsonPanel from "./JsonPanel";
import ChatWidget from "./ChatWidget";
import { Bell, Bolt, Calendar, FileDoc, Gauge, Printer, Shield, Trend, Wallet } from "./Icons";

const TABS = ["Overview", "Bill lines", "Answers", "Checks", "Data"] as const;
type Tab = (typeof TABS)[number];

const PROVIDER_NAME: Record<string, string> = { KE: "K-Electric", IESCO: "IESCO", LESCO: "LESCO" };

function delta(now: number, before: number): string {
  if (!before) return "—";
  const p = ((now - before) / before) * 100;
  return `${p > 0 ? "+" : ""}${p.toFixed(0)}%`;
}

interface Props { data: Analysis; image?: string; isPdf?: boolean }

export default function BillView({ data, image, isPdf = false }: Props) {
  const { bill, summary: s, checks } = data;
  const [tab, setTab] = useState<Tab>("Overview");
  const [printing, setPrinting] = useState(false);
  const units = bill.units_consumed;
  const shown = checks.filter((c) => c.status !== "skip");
  const failed = shown.filter((c) => c.status === "fail").length;
  const warned = shown.filter((c) => c.status === "warn").length;
  const tiers = bill.late_payment_tiers;
  const provider = PROVIDER_NAME[bill.provider ?? ""] ?? bill.provider ?? "Bill";

  useEffect(() => { setTab("Overview"); }, [data.image_hash]);

  useEffect(() => {
    if (!printing) return;
    const done = () => setPrinting(false);
    window.addEventListener("afterprint", done);
    const t = setTimeout(() => window.print(), 150);
    return () => { clearTimeout(t); window.removeEventListener("afterprint", done); };
  }, [printing]);

  const addReminder = () => {
    const ics = dueDateIcs(bill, rs(bill.payable_within_due_date));
    if (!ics) return toast("This bill has no due date to remind you about.", "error");
    download(`${provider}-bill-due-${bill.due_date}.ics`, ics, "text/calendar;charset=utf-8");
    toast("Reminder downloaded. Open it to add it to your calendar.");
  };

  const stats = [
    { icon: Bolt, tone: "green", value: `${num(units)} units`, label: s.units_last_month != null && units != null ? `${delta(units, s.units_last_month)} vs last month` : "used this month" },
    { icon: Gauge, tone: "teal", value: rs(s.average_cost_per_unit, 2), label: "average cost per unit" },
    { icon: Trend, tone: "ruby", value: s.units_same_month_last_year != null && units != null ? delta(units, s.units_same_month_last_year) : "—", label: s.units_same_month_last_year != null ? `vs ${num(s.units_same_month_last_year)} units a year ago` : "no data for last year" },
    { icon: Calendar, tone: "amber", value: s.forecast_next_month_units != null ? `~${num(s.forecast_next_month_units)} units` : "—", label: "expected next month" },
  ];

  const badge = failed
    ? `${failed} check${failed > 1 ? "s" : ""} need attention`
    : warned
      ? `${shown.length - warned} of ${shown.length} checks passed`
      : `${shown.length} of ${shown.length} checks passed`;

  const show = (t: Tab) => printing || tab === t;

  return (
    <article className={`result${printing ? " printing" : ""}`}>
      <section className="summary-row">
        <div className="summary">
          <div className="summary-top">
            <span className="summary-provider">{provider}</span>
            <button className={`verified ${failed ? "bad" : warned ? "warnish" : ""}`} onClick={() => setTab("Checks")}>
              <Shield /> {badge}
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
          <div className="summary-bottom">
            <dl className="summary-facts">
              <div><dt>Tariff</dt><dd>{bill.tariff ?? "—"}</dd></div>
              <div><dt>Load</dt><dd>{bill.sanctioned_load_kw != null ? `${num(bill.sanctioned_load_kw, 2)} kW` : "—"}</dd></div>
              <div><dt>Issued</dt><dd>{dayLabel(bill.issue_date)}</dd></div>
              {bill.connection_category && <div><dt>Category</dt><dd>{bill.connection_category}</dd></div>}
            </dl>
            <div className="summary-actions no-print">
              <button className="glass-btn" onClick={addReminder}><Bell /> Remind me</button>
              <button className="glass-btn" onClick={() => setPrinting(true)}><Printer /> Print report</button>
            </div>
          </div>
        </div>
        {(image || isPdf) && (
          <figure className="thumb card no-print">
            {image ? <img src={image} alt="The uploaded bill" /> : <div className="thumb-doc"><FileDoc /><span>PDF bill</span></div>}
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

      <div className="tabs no-print" role="tablist" aria-label="Bill details">
        {TABS.map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}>
            {t}{t === "Answers" ? ` (${data.answers.length})` : t === "Checks" && (failed || warned) ? " !" : ""}
          </button>
        ))}
      </div>

      <div className="tab-body">
        {show("Overview") && (
          <>
            <Insights items={data.insights ?? []} />
            <Reconciliation data={data} />
            <UsageChart series={s.series} average={s.average_units_previous_12} />
          </>
        )}
        {show("Bill lines") && <LineItems bill={bill} />}
        {show("Answers") && <Answers answers={data.answers} />}
        {show("Checks") && <Checks checks={checks} attempts={data.attempts} cached={data.cached} />}
        {!printing && tab === "Data" && <JsonPanel data={data} />}
      </div>
      <div className="no-print"><ChatWidget bill={bill} /></div>
      {printing && <p className="print-foot">Generated by Billsight from the uploaded bill. Figures are copied from the bill and checked against its printed totals.</p>}
    </article>
  );
}
