import { useEffect, useState } from "react";
import { analyzeBill } from "../api";
import type { Analysis } from "../types";
import Dropzone from "./Dropzone";
import Landing from "./Landing";
import BillView from "./BillView";

export default function SingleBill() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<Analysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

  const run = async (f: File, useCache = true) => {
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setError(null);
    setBusy(true);
    try {
      setResult(await analyzeBill(f, useCache));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  if (!file) return <Landing onFile={(f) => run(f)} />;

  return (
    <div className="single">
      <div className="toolbar">
        <p className="file-name">{file.name}</p>
        <div className="toolbar-actions">
          {result && !busy && <button className="btn ghost" onClick={() => run(file, false)}>Read again</button>}
          <Dropzone compact onFiles={([f]) => run(f)} title="" hint="" />
        </div>
      </div>

      {busy && (
        <div className="reading card">
          {preview && (
            <div className="scan">
              <img src={preview} alt="Uploaded bill" />
              <span className="scanline" aria-hidden="true" />
            </div>
          )}
          <div>
            <p className="reading-title">Reading your bill</p>
            <ol className="reading-steps">
              <li>Copying every charge, tax and reading</li>
              <li>Checking the totals add up</li>
              <li>Working out your answers</li>
            </ol>
            <p className="muted small">Usually 5 to 20 seconds.</p>
          </div>
        </div>
      )}

      {error && (
        <div className="banner error">
          {error} <button className="link" onClick={() => run(file, false)}>Try again</button>
        </div>
      )}
      {result && <BillView data={result} image={preview ?? undefined} />}
    </div>
  );
}
