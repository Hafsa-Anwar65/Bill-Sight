import { useState } from "react";
import { exportCsv } from "../api";
import type { Analysis } from "../types";
import { download } from "../format";

export default function JsonPanel({ data }: { data: Analysis }) {
  const [copied, setCopied] = useState(false);
  const json = JSON.stringify(data.level1, null, 2);

  const copy = async () => {
    await navigator.clipboard.writeText(json);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const csv = async () => {
    const out = await exportCsv([{ bill_id: data.bill_id, bill: data.bill }]);
    download(`${data.bill_id}_level1.csv`, out.level1_csv);
    download(`${data.bill_id}_level2.csv`, out.level2_csv);
  };

  return (
    <section className="card pad json">
      <div className="panel-head">
        <h3>Extracted data</h3>
        <p className="muted">WTQ Level 1 format</p>
      </div>
      <div className="json-actions top">
        <button className="btn" onClick={copy}>{copied ? "Copied" : "Copy JSON"}</button>
        <button className="btn" onClick={csv}>Download CSVs for this bill</button>
      </div>
      <pre>{json}</pre>
    </section>
  );
}
