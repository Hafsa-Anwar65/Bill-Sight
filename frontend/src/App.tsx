import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { getHealth } from "./api";
import { AuthProvider, useAuth } from "./auth";
import SingleBill from "./components/SingleBill";
import BatchRun from "./components/BatchRun";
import MyBills from "./components/MyBills";
import AuthModal from "./components/AuthModal";
import ErrorBoundary from "./components/ErrorBoundary";
import Toaster from "./components/Toaster";
import { Bolt, Folder, LogOut, Moon, Sun, Upload } from "./components/Icons";
import { applyTheme, initialTheme, type Theme } from "./theme";
import { toast } from "./toast";

const Background3D = lazy(() => import("./components/Background3D"));

type Mode = "single" | "batch" | "mine";

function UserMenu({ onMyBills }: { onMyBills: () => void }) {
  const { user, signOut, openAuth } = useAuth();
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => { if (!box.current?.contains(e.target as Node)) setOpen(false); };
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", close);
    window.addEventListener("keydown", esc);
    return () => { document.removeEventListener("mousedown", close); window.removeEventListener("keydown", esc); };
  }, [open]);

  if (!user) return <button className="btn ghost header-signin" onClick={() => openAuth("signin")}>Sign in</button>;

  const initials = user.name.split(/\s+/).map((w) => w[0]).join("").slice(0, 2).toUpperCase();
  return (
    <div className="user-menu" ref={box}>
      <button className="avatar" onClick={() => setOpen((o) => !o)} aria-expanded={open} aria-label="Account menu">{initials}</button>
      {open && (
        <div className="menu card" role="menu">
          <div className="menu-head"><p className="menu-name">{user.name}</p><p className="muted small">{user.email}</p></div>
          <button role="menuitem" onClick={() => { setOpen(false); onMyBills(); }}><Folder /> My bills</button>
          <button role="menuitem" onClick={async () => { setOpen(false); await signOut(); toast("Signed out"); }}><LogOut /> Sign out</button>
        </div>
      )}
    </div>
  );
}

function Shell() {
  const { user } = useAuth();
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

  const go = (m: Mode) => { setMode(m); window.scrollTo({ top: 0 }); };
  const goHome = () => { setMode("single"); setResetKey((k) => k + 1); window.scrollTo({ top: 0 }); };
  const howItWorks = () => {
    if (mode !== "single") goHome();
    setTimeout(() => document.getElementById("how")?.scrollIntoView({ behavior: "smooth" }), 50);
  };

  return (
    <>
      <Suspense fallback={null}><Background3D theme={theme} /></Suspense>
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
            {user
              ? <button aria-current={mode === "mine"} onClick={() => go("mine")}>My bills</button>
              : <button onClick={howItWorks}>How it works</button>}
            <button aria-current={mode === "batch"} onClick={() => go("batch")}>Batch export</button>
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
            <UserMenu onMyBills={() => go("mine")} />
            <button className="btn primary header-cta" onClick={goHome}>
              <Upload /> <span className="cta-text">Upload bill</span>
            </button>
          </div>
        </div>
      </header>

      <div className="app">
        {problem && <p className="banner error">{problem}</p>}
        <main>
          <ErrorBoundary key={`${mode}-${resetKey}`}>
            {mode === "single" && <SingleBill key={resetKey} onMyBills={() => go("mine")} />}
            {mode === "batch" && <BatchRun />}
            {mode === "mine" && <MyBills />}
          </ErrorBoundary>
        </main>
      </div>

      <AuthModal />
      <Toaster />
      <footer className="footer">
        <div className="footer-inner">
          <span className="brand-mini"><span className="brand-mark sm"><Bolt /></span> Billsight</span>
          <span>Supports K-Electric, IESCO, LESCO and other DISCO bills. Personal details on the bill are never stored.</span>
        </div>
      </footer>
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}
