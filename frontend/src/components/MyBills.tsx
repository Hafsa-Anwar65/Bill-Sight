import { useCallback, useEffect, useRef, useState } from "react";
import { deleteBill, getSavedBill, listBills, type SavedBill } from "../api";
import { useAuth } from "../auth";
import type { Analysis } from "../types";
import { dayLabel, monthLabel, num, rs } from "../format";
import { toast } from "../toast";
import BillView from "./BillView";
import { ArrowLeft, Folder, Trash, UserIcon } from "./Icons";

const PROVIDER_NAME: Record<string, string> = { KE: "K-Electric" };

function TrendChart({ bills }: { bills: SavedBill[] }) {
  const box = useRef<HTMLDivElement>(null);
  const [W, setW] = useState(720);
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setW(Math.max(280, e.contentRect.width)));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const points = bills.filter((b) => b.bill_month && b.payable != null).slice(0, 24).reverse();
  if (points.length < 2) return null;
  const H = 220, top = 24, bottom = 28;
  const max = Math.max(...points.map((p) => Math.abs(p.payable!))) * 1.15 || 1;
  const step = W / points.length;
  const bw = Math.min(44, step * 0.6);
  const short = (v: number) => (Math.abs(v) >= 1000 ? `${Math.round(v / 100) / 10}k` : num(v));

  return (
    <section className="card pad">
      <div className="panel-head"><h3>Amount payable, bill by bill</h3><p className="muted">Oldest to newest</p></div>
      <div ref={box}>
        <svg className="chart" width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Payable amount per saved bill">
          <defs>
            <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3cb371" />
              <stop offset="100%" stopColor="#1f6f47" />
            </linearGradient>
          </defs>
          {points.map((p, i) => {
            const h = (Math.max(p.payable!, 0) / max) * (H - top - bottom);
            const x = i * step + (step - bw) / 2;
            const y = H - bottom - h;
            return (
              <g key={p.id} className="trend-bar">
                <title>{`${monthLabel(p.bill_month, true)}: ${rs(p.payable)}`}</title>
                <rect x={x} y={y} width={bw} height={Math.max(h, 2)} rx={Math.min(6, bw / 3)} fill="url(#trendGrad)" />
                <text x={x + bw / 2} y={y - 7}>{short(p.payable!)}</text>
                <text x={x + bw / 2} y={H - 8}>{monthLabel(p.bill_month)}</text>
              </g>
            );
          })}
        </svg>
      </div>
    </section>
  );
}

export default function MyBills() {
  const { user, ready, openAuth } = useAuth();
  const [bills, setBills] = useState<SavedBill[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<Analysis | null>(null);
  const [confirming, setConfirming] = useState<number | null>(null);

  const load = useCallback(() => {
    setError(null);
    listBills().then((r) => setBills(r.bills)).catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => { if (user) load(); else setBills(null); }, [user, load]);

  if (!ready) return <p className="muted">Loading…</p>;

  if (!user) {
    return (
      <section className="card pad empty-state">
        <span className="chip-icon green"><UserIcon /></span>
        <h2>Keep all your bills in one place</h2>
        <p className="muted">Create a free account and every bill you analyse is saved, so you can compare months and reopen any bill later.</p>
        <div className="hero-actions">
          <button className="btn primary" onClick={() => openAuth("signup")}>Create account</button>
          <button className="btn ghost" onClick={() => openAuth("signin")}>Sign in</button>
        </div>
      </section>
    );
  }

  if (open) {
    return (
      <div className="single">
        <div className="toolbar">
          <button className="btn ghost" onClick={() => setOpen(null)}><ArrowLeft /> All my bills</button>
        </div>
        <BillView data={open} />
      </div>
    );
  }

  const openBill = async (id: number) => {
    try {
      setOpen(await getSavedBill(id));
      window.scrollTo({ top: 0 });
    } catch (e) {
      toast((e as Error).message, "error");
    }
  };

  const remove = async (id: number) => {
    if (confirming !== id) return setConfirming(id);
    try {
      await deleteBill(id);
      setBills((bs) => bs?.filter((b) => b.id !== id) ?? null);
      toast("Bill deleted");
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setConfirming(null);
    }
  };

  const list = bills ?? [];
  const withPay = list.filter((b) => b.payable != null && b.payable > 0);
  const withUnits = list.filter((b) => b.units != null);
  const total = withPay.reduce((a, b) => a + (b.payable ?? 0), 0);
  const avgUnits = withUnits.length ? withUnits.reduce((a, b) => a + (b.units ?? 0), 0) / withUnits.length : null;

  return (
    <section className="mybills">
      <div className="page-head">
        <h1>My bills</h1>
        <p className="lede">Every bill you analyse while signed in as {user.name} is saved here.</p>
      </div>

      {error && <p className="banner error">{error} <button className="link" onClick={load}>Try again</button></p>}
      {bills === null && !error && <p className="muted">Loading your bills…</p>}

      {bills !== null && list.length === 0 && (
        <section className="card pad empty-state">
          <span className="chip-icon green"><Folder /></span>
          <h2>No saved bills yet</h2>
          <p className="muted">Analyse a bill while signed in and it will appear here.</p>
        </section>
      )}

      {list.length > 0 && (
        <>
          <section className="stat-grid" aria-label="Totals">
            <div className="stat card"><p className="stat-value">{list.length}</p><p className="stat-label">bills saved</p></div>
            <div className="stat card"><p className="stat-value">{rs(Math.round(total))}</p><p className="stat-label">total payable across bills</p></div>
            <div className="stat card"><p className="stat-value">{avgUnits != null ? `${num(avgUnits)} units` : "—"}</p><p className="stat-label">average per bill</p></div>
            <div className="stat card"><p className="stat-value">{monthLabel(list[0].bill_month, true)}</p><p className="stat-label">latest bill</p></div>
          </section>

          <TrendChart bills={list} />

          <section className="card pad">
            <div className="panel-head"><h3>All bills</h3><p className="muted">Newest first</p></div>
            <div className="table-scroll">
              <table className="batch-table saved-table">
                <thead>
                  <tr><th scope="col">Month</th><th scope="col">Provider</th><th scope="col" className="amt">Units</th><th scope="col" className="amt">Payable</th><th scope="col">Saved</th><th scope="col"><span className="sr-only">Actions</span></th></tr>
                </thead>
                <tbody>
                  {list.map((b) => (
                    <tr key={b.id}>
                      <td><button className="link" onClick={() => openBill(b.id)}>{monthLabel(b.bill_month, true)}</button></td>
                      <td>{PROVIDER_NAME[b.provider ?? ""] ?? b.provider ?? "—"}</td>
                      <td className="amt">{num(b.units)}</td>
                      <td className="amt">{rs(b.payable)}</td>
                      <td className="muted">{dayLabel(b.saved_at.slice(0, 10))}</td>
                      <td className="row-actions">
                        <button className="btn ghost sm" onClick={() => openBill(b.id)}>Open</button>
                        <button className={`btn sm ${confirming === b.id ? "danger" : "ghost"}`} onClick={() => remove(b.id)}
                          onBlur={() => setConfirming(null)} aria-label={`Delete ${monthLabel(b.bill_month, true)} bill`}>
                          <Trash /> {confirming === b.id ? "Confirm" : ""}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </section>
  );
}
