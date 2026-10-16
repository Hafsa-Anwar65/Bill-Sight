import type { Insight } from "../types";
import { Alert, Check, Info, Piggy } from "./Icons";

const ICON = { save: Piggy, warn: Alert, good: Check, info: Info };

export default function Insights({ items }: { items: Insight[] }) {
  if (!items.length) return null;
  return (
    <section className="card pad">
      <div className="panel-head">
        <h3>What this bill tells you</h3>
        <p className="muted">Worked out from the numbers on your bill</p>
      </div>
      <ul className="insights">
        {items.map((it) => {
          const Icon = ICON[it.kind] ?? Info;
          return (
            <li key={it.title} className={`insight ${it.kind}`}>
              <span className="insight-icon"><Icon /></span>
              <div>
                <p className="insight-title">{it.title}</p>
                <p className="insight-detail">{it.detail}</p>
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
