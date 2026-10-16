import { useEffect, useState } from "react";
import { getHealth } from "./api";
import SingleBill from "./components/SingleBill";
import BatchRun from "./components/BatchRun";
import Background3D from "./components/Background3D";
import { Bolt, Moon, Sun, Upload } from "./components/Icons";
import { applyTheme, initialTheme, type Theme } from "./theme";

type Mode = "single" | "batch";

export default function App() {
  const [mode, setMode] = useState<Mode>("single");
  const [resetKey, setResetKey] = useState(0);
  const [problem, setProblem] = useState<string | null>(null);
  const [theme, setTheme] = useState<Theme>(initialTheme);

  useEffect(() => applyTheme(theme), [theme]);

  useEffect(() => {
    getHealth()
      .then((h) => !h.api_key_set && setProblem("Add GEMINI_API_KEY to the .env file in the project folder, then restart the server."))
      .catch((e: Error) => setProblem(e.message));
  }, []);

  const goHome = () => { setMode("single"); setResetKey((k) => k + 1); window.scrollTo({ top: 0 }); };
  const howItWorks = () => {
    if (mode !== "single") goHome();
    setTimeout(() => document.getElementById("how")?.scrollIntoView({ behavior: "smooth" }), 50);
  };

  return (
    <>
      <Background3D theme={theme} />
      <div className="bg-wash" aria-hidden="true" />
      <header className="topbar">
        <div className="topbar-inner">
          <button className="brand" onClick={goHome} aria-label="Billsight home">
            <span className="brand-mark"><Bolt /></span>
            <span className="brand-text">
              <span className="brand-name">Billsight</span>
              <span className="brand-tag">Electricity bill analysis</span>
            </span>
          </button>

          <nav className="nav" aria-label="Main">
            <button aria-current={mode === "single"} onClick={goHome}>Analyze</button>
            <button onClick={howItWorks}>How it works</button>
            <button aria-current={mode === "batch"} onClick={() => setMode("batch")}>Batch export</button>
          </nav>

          <div className="header-actions">
            <button
              className="theme-toggle"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
              title={theme === "dark" ? "Light theme" : "Dark theme"}
            >
              {theme === "dark" ? <Sun /> : <Moon />}
            </button>
            <button className="btn primary header-cta" onClick={goHome}>
              <Upload /> Upload bill
            </button>
          </div>
        </div>
      </header>

      <div className="app">
        {problem && <p className="banner error">{problem}</p>}
        <main>{mode === "single" ? <SingleBill key={resetKey} /> : <BatchRun />}</main>
      </div>

      <footer className="footer">
        <div className="footer-inner">
          <span className="brand-mini"><span className="brand-mark sm"><Bolt /></span> Billsight</span>
          <span>Supports K-Electric, IESCO, LESCO and other DISCO bills. Personal details on the bill are never stored.</span>
        </div>
      </footer>
    </>
  );
}
