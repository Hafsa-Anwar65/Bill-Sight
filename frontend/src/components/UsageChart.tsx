import { useEffect, useRef, useState } from "react";
import type { SeriesPoint } from "../types";
import { monthLabel, num } from "../format";

const H = 260;
const PAD = { top: 26, right: 4, bottom: 30, left: 4 };

export default function UsageChart({ series, average }: { series: SeriesPoint[]; average: number | null }) {
  const box = useRef<HTMLDivElement>(null);
  const [W, setW] = useState(720);

  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setW(Math.max(280, e.contentRect.width)));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const points = series.filter((p) => p.units != null);
  if (points.length < 2) return null;

  const max = Math.max(...points.map((p) => p.units!), average ?? 0) * 1.12;
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;
  const step = innerW / points.length;
  const bw = Math.min(44, step * 0.62);
  const y = (v: number) => PAD.top + innerH - (v / max) * innerH;
  const narrow = step < 34;

  return (
    <section className="card pad">
      <div className="panel-head">
        <h3>Units used, month by month</h3>
        {average != null && (
          <p className="legend"><span className="legend-line" /> Average of the previous {Math.min(12, points.length - 1)} months: {num(average, 1)} units</p>
        )}
      </div>
      <div ref={box}>
        <svg className="chart" width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Monthly units consumed">
          <defs>
            <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#a855f7" />
              <stop offset="100%" stopColor="#4f46e5" />
            </linearGradient>
          </defs>
          {average != null && (
            <line className="avg" x1={PAD.left} x2={W - PAD.right} y1={y(average)} y2={y(average)} />
          )}
          {points.map((p, i) => {
            const x = PAD.left + i * step + (step - bw) / 2;
            const top = y(p.units!);
            const showMonth = !narrow || i % 2 === points.length % 2 || p.current;
            return (
              <g key={p.month} className={p.current ? "bar current" : "bar"}>
                <title>{`${monthLabel(p.month, true)}: ${num(p.units)} units`}</title>
                <rect x={x} y={top} width={bw} height={PAD.top + innerH - top} rx={Math.min(6, bw / 3)} />
                {(!narrow || p.current) && <text className="v" x={x + bw / 2} y={top - 8}>{num(p.units)}</text>}
                {showMonth && <text className="m" x={x + bw / 2} y={H - 8}>{monthLabel(p.month)}</text>}
              </g>
            );
          })}
        </svg>
      </div>
    </section>
  );
}
