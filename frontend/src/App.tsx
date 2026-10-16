import { useEffect, useState } from "react";
import { getHealth } from "./api";
import type { Health } from "./types";
import SingleBill from "./components/SingleBill";
import BatchRun from "./components/BatchRun";
import { Bolt } from "./components/Icons";

type Mode = "single" | "batch";

export default function App() {
  const [mode, setMode] = useState<Mode>("single");
  const [resetKey, setResetKey] = useState(0);
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch((e: Error) => setHealthError(e.message));
  }, []);

  const goHome = () => { setMode("single"); setResetKey((k) => k + 1); };

  return (
    <>
      <div className="blobs" aria-hidden="true"><span /><span /><span /></div>
      <header className="topbar">
        <div className="topbar-inner">
          <button className="brand" onClick={goHome}>
            <span className="brand-mark"><Bolt /></span>
            Billsight
          </button>
          <nav className="nav" aria-label="Main">
            <button aria-current={mode === "single"} onClick={() => setMode("single")}>Analyze a bill</button>
            <button aria-current={mode === "batch"} onClick={() => setMode("batch")}>Batch export</button>
          </nav>
          <span className={`status ${health?.api_key_set ? "ok" : "bad"}`} role="status">
            {health ? (health.api_key_set ? health.model : "API key missing") : healthError ? "Server offline" : "Connecting"}
          </span>
        </div>
      </header>

      <div className="app">
        {healthError && <p className="banner error">{healthError}</p>}
        {health && !health.api_key_set && (
          <p className="banner error">Add GEMINI_API_KEY to the .env file in the project folder, then restart the server.</p>
        )}
        <main>{mode === "single" ? <SingleBill key={resetKey} /> : <BatchRun />}</main>
      </div>
    </>
  );
}
