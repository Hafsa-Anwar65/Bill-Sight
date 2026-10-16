import type { Check } from "../types";

const ICON: Record<Check["status"], string> = { pass: "✓", warn: "!", fail: "✕", skip: "–" };

export default function Checks({ checks, attempts, cached }: { checks: Check[]; attempts: number; cached: boolean }) {
  const shown = checks.filter((c) => c.status !== "skip");
  const failed = shown.filter((c) => c.status === "fail").length;
  return (
    <section className="card pad checks" aria-label="Accuracy checks">
      <h3>{failed ? `${failed} check${failed > 1 ? "s" : ""} failed` : `${shown.length} of ${shown.length} checks passed`}</h3>
      <p className="muted small">
        {cached ? "Loaded from cache." : `Read in ${attempts} attempt${attempts > 1 ? "s" : ""}.`} Totals on the bill are used to verify the reading.
      </p>
      <ul>
        {shown.map((c) => (
          <li key={c.id} className={c.status}>
            <span className="icon" aria-label={c.status}>{ICON[c.status]}</span>
            <div>
              <p className="check-label">{c.label}</p>
              <p className="check-detail">{c.detail}</p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
