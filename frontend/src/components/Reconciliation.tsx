import type { Analysis } from "../types";
import { rs } from "../format";

/** Shows that the extracted lines add up to the amount printed on the bill. */
export default function Reconciliation({ data }: { data: Analysis }) {
  const { bill, checks } = data;
  const subsidy = bill.charges.filter((c) => c.type === "subsidy").reduce((a, c) => a + c.amount, 0);
  const charges = bill.charges.filter((c) => c.type !== "subsidy").reduce((a, c) => a + c.amount, 0);
  const taxes = bill.taxes.reduce((a, t) => a + t.amount, 0);
  const carried = (bill.arrears ?? 0) + (bill.other_adjustments ?? 0);
  const payable = bill.payable_within_due_date;
  const check = checks.find((c) => c.id === "payable");

  const parts = [
    { key: "charges", label: "Electricity charges", value: charges, sign: "" },
    ...(subsidy ? [{ key: "subsidy", label: "Subsidy", value: subsidy, sign: "−" }] : []),
    { key: "taxes", label: "Taxes and duties", value: taxes, sign: "+" },
    ...(Math.abs(carried) >= 1 ? [{ key: "carried", label: carried > 0 ? "Arrears" : "Credit", value: carried, sign: carried > 0 ? "+" : "−" }] : []),
  ];
  const positive = parts.filter((p) => p.value > 0).reduce((a, p) => a + p.value, 0) || 1;

  return (
    <section className="card pad recon" aria-label="How the payable amount adds up">
      <div className="panel-head">
        <h3>How your total adds up</h3>
      </div>
      <div className="recon-bar" aria-hidden="true">
        {parts.filter((p) => p.value > 0).map((p) => (
          <span key={p.key} className={`seg ${p.key}`} style={{ flexGrow: p.value / positive }} />
        ))}
      </div>
      <ol className="recon-sum">
        {parts.map((p) => (
          <li key={p.key} className={p.key}>
            <span className="op">{p.sign}</span>
            <span className="recon-label">{p.label}</span>
            <span className="recon-value">{rs(Math.abs(p.value), 2)}</span>
          </li>
        ))}
        <li className="total">
          <span className="op">=</span>
          <span className="recon-label">Payable on the bill</span>
          <span className="recon-value">{rs(payable)}</span>
        </li>
      </ol>
      {check && (
        <p className={`recon-verdict ${check.status}`}>
          {check.status === "pass"
            ? "The lines read from the bill add up to the printed payable amount (rounded to the rupee)."
            : `These lines do not add up to the printed amount. ${check.detail}`}
        </p>
      )}
    </section>
  );
}
