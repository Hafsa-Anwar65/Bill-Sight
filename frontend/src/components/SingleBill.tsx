import { useCallback, useEffect, useState } from "react";
import { analyzeBill } from "../api";
import type { Analysis } from "../types";
import { isPdf } from "../format";
import { saveRecent } from "../storage";
import { toast } from "../toast";
import Dropzone, { pickValid } from "./Dropzone";
import Landing from "./Landing";
import BillView from "./BillView";
import { FileDoc, Refresh } from "./Icons";

interface Source { name: string; file: File | null; preview: string | null; pdf: boolean }

export default function SingleBill() {
  const [source, setSource] = useState<Source | null>(null);
  const [result, setResult] = useState<Analysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => () => { if (source?.preview) URL.revokeObjectURL(source.preview); }, [source]);

  const run = useCallback(async (f: File, useCache = true) => {
    const pdf = isPdf(f);
    setSource({ name: f.name, file: f, preview: pdf ? null : URL.createObjectURL(f), pdf });
    setResult(null);
    setError(null);
    setBusy(true);
    window.scrollTo({ top: 0, behavior: "smooth" });
    try {
      const data = await analyzeBill(f, useCache);
      setResult(data);
      saveRecent(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, []);

  // Paste a screenshot of the bill (Ctrl + V) anywhere on the page.
  useEffect(() => {
    const onPaste = (e: ClipboardEvent) => {
      if (busy) return;
      const target = e.target as HTMLElement | null;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA")) return;
      const files = pickValid(Array.from(e.clipboardData?.files ?? []));
      if (files.length) {
        e.preventDefault();
        const f = files[0];
        const named = f.name && f.name !== "image.png" ? f : new File([f], `pasted-bill-${Date.now()}.png`, { type: f.type });
        toast("Pasted image received");
        run(named);
      }
    };
    window.addEventListener("paste", onPaste);
    return () => window.removeEventListener("paste", onPaste);
  }, [busy, run]);

  const openSaved = (data: Analysis) => {
    setSource({ name: `${data.bill_id} (saved)`, file: null, preview: null, pdf: false });
    setError(null);
    setResult(data);
    window.scrollTo({ top: 0 });
  };

  if (!source) return <Landing onFile={(f) => run(f)} onOpen={openSaved} />;

  return (
    <div className="single">
      <div className="toolbar">
        <p className="file-name">{source.name}</p>
        <div className="toolbar-actions">
          {source.file && !busy && (
            <button className="btn ghost" onClick={() => source.file && run(source.file, false)}><Refresh /> Read again</button>
          )}
          <Dropzone compact onFiles={([f]) => run(f)} title="" hint="" />
        </div>
      </div>

      {busy && (
        <div className="reading card">
          <div className="scan">
            {source.preview ? <img src={source.preview} alt="Uploaded bill" /> : <div className="scan-doc"><FileDoc /><span>PDF bill</span></div>}
            <span className="scanline" aria-hidden="true" />
          </div>
          <div>
            <p className="reading-title">Reading your bill</p>
            <ol className="reading-steps">
              <li>Copying every charge, tax and reading</li>
              <li>Checking that the totals add up</li>
              <li>Working out your answers and tips</li>
            </ol>
            <p className="muted small">Usually 5 to 20 seconds. If a total doesn't match, the bill is read again automatically.</p>
          </div>
        </div>
      )}

      {error && (
        <div className="banner error">
          <span>{error}</span>
          {source.file && <button className="link" onClick={() => source.file && run(source.file, false)}>Try again</button>}
        </div>
      )}
      {result && <BillView data={result} image={source.preview ?? undefined} isPdf={source.pdf} />}
    </div>
  );
}
