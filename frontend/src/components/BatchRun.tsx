import { useState } from "react";
import { analyzeBill, exportCsv } from "../api";
import type { Analysis } from "../types";
import { download, monthLabel, num, rs } from "../format";
import Dropzone from "./Dropzone";
import BillView from "./BillView";

interface Row {
  id: string;
  file: File;
  state: "waiting" | "reading" | "done" | "error";
  result?: Analysis;
  error?: string;
}

const WORKERS = 2;
const idOf = (f: File) => f.name.replace(/\.[^.]+$/, "");

export default function BatchRun() {
  const [rows, setRows] = useState<Row[]>([]);
  const [running, setRunning] = useState(false);
  const [open, setOpen] = useState<string | null>(null);

  const update = (id: string, patch: Partial<Row>) =>
    setRows((prev) => prev.map((r) => (r.id === id ? { ...r, ...patch } : r)));

  const start = async (files: File[]) => {
    const queue: Row[] = files
      .map((file) => ({ id: idOf(file), file, state: "waiting" as const }))
      .sort((a, b) => a.id.localeCompare(b.id));
    setRows(queue);
    setOpen(null);
    setRunning(true);
    let next = 0;
    const worker = async () => {
      while (next < queue.length) {
        const row = queue[next++];
        update(row.id, { state: "reading" });
        try {
          update(row.id, { state: "done", result: await analyzeBill(row.file) });
        } catch (e) {
          update(row.id, { state: "error", error: (e as Error).message });
        }
      }
    };
    await Promise.all(Array.from({ length: WORKERS }, worker));
    setRunning(false);
  };

  const exportAll = async () => {
    const out = await exportCsv(rows.map((r) => ({ bill_id: r.id, bill: r.result?.bill ?? null })));
    download("level1.csv", out.level1_csv);
    download("level2.csv", out.level2_csv);
  };

  const done = rows.filter((r) => r.state === "done").length;
  const selected = rows.find((r) => r.id === open)?.result;

  return (
    <section className="batch">
      <div className="page-head">
        <h1>Batch export for the submission</h1>
        <p className="lede">
          Name each image by its bill ID (for example <code>IESCO_0002.jpg</code>). You get level1.csv with the
          extracted JSON and level2.csv with all 12 answers per bill.
        </p>
      </div>
      <Dropzone multiple onFiles={start} title="Drop all bill images here" hint="They are read two at a time." />

      {rows.length > 0 && (
        <div className="card pad">
          <div className="panel-head row">
            <h3>{running ? `Reading ${done} of ${rows.length}` : `${done} of ${rows.length} bills read`}</h3>
            <button className="btn primary" disabled={running || !done} onClick={exportAll}>Download level1.csv and level2.csv</button>
          </div>
          <div className="progress" aria-hidden="true"><span style={{ width: `${(done / rows.length) * 100}%` }} /></div>
          <div className="table-scroll"><table className="batch-table">
            <thead>
              <tr><th scope="col">Bill ID</th><th scope="col">Provider</th><th scope="col">Month</th><th scope="col" className="amt">Units</th><th scope="col" className="amt">Payable</th><th scope="col">Checks</th></tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const b = r.result?.bill;
                const bad = r.result?.checks.filter((c) => c.status === "fail" || c.status === "warn") ?? [];
                return (
                  <tr key={r.id} className={open === r.id ? "selected" : ""}>
                    <td>
                      {r.result ? (
                        <button className="link" onClick={() => setOpen(open === r.id ? null : r.id)}>{r.id}</button>
                      ) : r.id}
                    </td>
                    <td>{b?.provider ?? ""}</td>
                    <td>{b ? monthLabel(b.bill_month, true) : ""}</td>
                    <td className="amt">{b ? num(b.units_consumed) : ""}</td>
                    <td className="amt">{b ? rs(b.payable_within_due_date) : ""}</td>
                    <td>
                      {r.state === "waiting" && <span className="muted">Waiting</span>}
                      {r.state === "reading" && <span className="muted">Reading…</span>}
                      {r.state === "error" && <span className="tag fail" title={r.error}>Failed: {r.error}</span>}
                      {r.state === "done" && (bad.length
                        ? <span className="tag warn">{bad.map((c) => c.label).join(", ")}</span>
                        : <span className="tag pass">All passed</span>)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table></div>
        </div>
      )}
      {selected && <BillView data={selected} />}
    </section>
  );
}
