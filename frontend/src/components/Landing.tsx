import { useEffect, useRef, useState } from "react";
import { loadSamples, type Sample } from "../samples";
import { STATIC_DEMO } from "../env";
import type { Analysis } from "../types";
import { dayLabel, monthLabel, rs } from "../format";
import { clearRecent, loadRecent } from "../storage";
import { useAuth } from "../auth";
import Dropzone, { ACCEPT, pickValid } from "./Dropzone";
import { Bolt, Calendar, Check, Clock, Percent, Receipt, Shield, Sparkle, Upload } from "./Icons";

const PROVIDERS = [
  { name: "K-Electric", region: "Karachi", tone: "ke" },
  { name: "IESCO", region: "Islamabad and Rawalpindi", tone: "iesco" },
  { name: "LESCO", region: "Lahore", tone: "lesco" },
];

const STEPS = [
  { icon: Upload, title: "Upload", text: "Take a clear photo of the full bill, or use a scan." },
  { icon: Shield, title: "Verify", text: "Every line is read and matched against the totals printed on the bill." },
  { icon: Sparkle, title: "Understand", text: "See where your money goes and get 12 common questions answered." },
];

const MOCK = [
  { icon: Bolt, k: "Units", v: "159", tone: "green" },
  { icon: Receipt, k: "Charges", v: "Rs 6,359", tone: "teal" },
  { icon: Percent, k: "Taxes", v: "Rs 1,261", tone: "ruby" },
  { icon: Calendar, k: "Due date", v: "22 Sep", tone: "amber" },
];

const PROVIDER_NAME: Record<string, string> = { KE: "K-Electric" };

export default function Landing({ onFile, onOpen, onMyBills, onSample }: { onFile: (f: File) => void; onOpen: (d: Analysis) => void; onMyBills: () => void; onSample: (slug: string) => void }) {
  const { user } = useAuth();
  const picker = useRef<HTMLInputElement>(null);
  const upload = () => picker.current?.click();
  const [recent, setRecent] = useState(loadRecent);
  const [samples, setSamples] = useState<Sample[]>([]);
  useEffect(() => { loadSamples().then(setSamples); }, []);

  return (
    <div className="landing">
      <section className="hero">
        <div className="hero-copy">
          <span className="pill"><Shield /> Every number checked against your bill</span>
          <h1>Making electricity bills easy to understand</h1>
          <p className="lede">
            Upload your K-Electric, IESCO or LESCO bill. Billsight reads every line, confirms it adds up, and
            explains what you pay for in plain words.
          </p>
          <p className="hint-line">Photo, scan or PDF. You can also paste a screenshot with Ctrl + V.</p>
          <div className="hero-actions">
            {STATIC_DEMO && samples[0] ? (
              <button className="btn primary lg" onClick={() => onSample(samples[0].slug)}>See a sample bill</button>
            ) : (
              <button className="btn primary lg" onClick={upload}><Upload /> Upload a bill</button>
            )}
            <a className="btn ghost lg" href="#samples">Try a sample</a>
          </div>
          <input
            ref={picker}
            type="file"
            accept={ACCEPT}
            hidden
            onChange={(e) => { const [f] = pickValid(e.target.files); if (f) onFile(f); e.target.value = ""; }}
          />
        </div>

        <div className="hero-art" aria-hidden="true">
          <div className="mock">
            <div className="mock-head">
              <span className="mock-badge"><Bolt /></span>
              <div>
                <p className="mock-title">Electricity bill</p>
                <p className="mock-sub">September 2026</p>
              </div>
            </div>
            {MOCK.map(({ icon: Icon, k, v, tone }) => (
              <div className="mock-row" key={k}>
                <span className={`chip-icon ${tone}`}><Icon /></span>
                <span className="mock-key">{k}</span>
                <span className="mock-val">{v}</span>
                <span className="tick"><Check /></span>
              </div>
            ))}
            <div className="mock-total"><span>Total payable</span><strong>Rs 7,621</strong></div>
          </div>
          <div className="float-card">
            <span className="float-icon"><Check /></span>
            <div><strong>9 of 9 checks</strong><p>Adds up to the bill</p></div>
          </div>
        </div>
      </section>

      {recent.length > 0 && (
        <section className="recent" aria-label="Recent bills">
          <div className="panel-head row">
            <h2 className="section-title"><Clock /> Recent bills on this device</h2>
            <span className="recent-links">
              {user && <button className="link" onClick={onMyBills}>All my saved bills</button>}
              <button className="link" onClick={() => { clearRecent(); setRecent([]); }}>Clear</button>
            </span>
          </div>
          <div className="recent-grid">
            {recent.map(({ data, savedAt }) => (
              <button key={data.image_hash} className="recent-card" onClick={() => onOpen(data)}>
                <span className="recent-top">
                  <span className="recent-provider">{PROVIDER_NAME[data.bill.provider ?? ""] ?? data.bill.provider ?? "Bill"}</span>
                  <span className="muted small">Opened {dayLabel(savedAt.slice(0, 10))}</span>
                </span>
                <span className="recent-month">{monthLabel(data.bill.bill_month, true)}</span>
                <span className="recent-amount">{rs(data.bill.payable_within_due_date)}</span>
              </button>
            ))}
          </div>
        </section>
      )}

      {samples.length > 0 && (
        <section className="recent" id="samples" aria-label="Sample bills">
          <div className="panel-head row">
            <h2 className="section-title"><Sparkle /> Try a sample bill</h2>
            <span className="muted small">Real bill layouts, personal details removed</span>
          </div>
          <div className="recent-grid">
            {samples.map((s) => (
              <button key={s.slug} className="recent-card" onClick={() => onSample(s.slug)}>
                <span className="recent-top">
                  <span className="recent-provider">{PROVIDER_NAME[s.provider ?? ""] ?? s.provider}</span>
                  <span className="muted small">{s.units} units</span>
                </span>
                <span className="recent-month">{monthLabel(s.bill_month, true)}</span>
                <span className="recent-amount">{rs(s.payable)}</span>
              </button>
            ))}
          </div>
        </section>
      )}

      <section className="providers" aria-label="Supported providers">
        {PROVIDERS.map((p) => (
          <button key={p.name} className="provider-card" onClick={upload}>
            <span className={`provider-logo ${p.tone}`}><Bolt /></span>
            <span className="provider-text">
              <span className="provider-name">{p.name}</span>
              <span className="provider-region">{p.region}</span>
            </span>
            <span className="provider-cta">Analyze</span>
          </button>
        ))}
      </section>

      <section className="how" id="how">
        <h2>How it works</h2>
        <p className="section-lede">Three steps, about 15 seconds.</p>
        <ol className="steps">
          {STEPS.map(({ icon: Icon, title, text }, i) => (
            <li key={title}>
              <span className="step-icon"><Icon /></span>
              <p className="step-n">Step {i + 1}</p>
              <h3>{title}</h3>
              <p>{text}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="upload-band">
        <Dropzone
          onFiles={([f]) => onFile(f)}
          title="Drop your bill here"
          hint="PNG, JPG, WEBP or PDF up to 15 MB. A straight, well-lit photo of the full page works best."
        />
      </section>
    </div>
  );
}
