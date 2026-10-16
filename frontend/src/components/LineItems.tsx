import type { Bill, LineItem } from "../types";
import { TYPE_LABEL, monthLabel, rs } from "../format";

function Group({ title, items, total }: { title: string; items: LineItem[]; total: number }) {
  return (
    <tbody>
      <tr className="group"><th colSpan={3} scope="colgroup">{title}</th></tr>
      {items.map((it, i) => (
        <tr key={i}>
          <td>{it.label}</td>
          <td className="muted">{TYPE_LABEL[it.type] ?? it.type}</td>
          <td className={`amt${it.amount < 0 ? " neg" : ""}`}>{rs(it.amount, 2)}</td>
        </tr>
      ))}
      <tr className="subtotal"><td colSpan={2}>Total {title.toLowerCase()}</td><td className="amt">{rs(total, 2)}</td></tr>
    </tbody>
  );
}

export default function LineItems({ bill }: { bill: Bill }) {
  const sum = (xs: LineItem[]) => xs.reduce((a, x) => a + x.amount, 0);
  const regs = bill.meter_registers;
  return (
    <section className="card pad">
      <div className="panel-head">
        <h3>Every line on the bill</h3>
        {bill.fpa_reference_month && <p className="muted">Fuel adjustment relates to {monthLabel(bill.fpa_reference_month, true)}</p>}
      </div>
      {regs.length > 0 && (
        <div className="registers">
          {regs.map((r) => (
            <p key={r.name}>
              <span className="muted">{r.name} reading</span> {r.previous ?? "—"} to {r.current ?? "—"}
              <strong> {r.units ?? "—"} units</strong>
            </p>
          ))}
        </div>
      )}
      <table className="lines">
        <thead><tr><th scope="col">As printed</th><th scope="col">Type</th><th scope="col" className="amt">Amount</th></tr></thead>
        <Group title="Charges" items={bill.charges} total={sum(bill.charges)} />
        <Group title="Taxes" items={bill.taxes} total={sum(bill.taxes)} />
      </table>
    </section>
  );
}
