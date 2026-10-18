import { useEffect, useRef, useState, type FormEvent } from "react";
import { signIn, signUp } from "../api";
import { useAuth } from "../auth";
import { toast } from "../toast";
import { Bolt, Close, Eye } from "./Icons";

export default function AuthModal() {
  const { authMode, closeAuth, setUser, openAuth } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const first = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!authMode) return;
    setError(null);
    setTimeout(() => first.current?.focus(), 30);
    const esc = (e: KeyboardEvent) => e.key === "Escape" && closeAuth();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [authMode, closeAuth]);

  if (!authMode) return null;
  const isSignup = authMode === "signup";

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setError(null);
    if (isSignup && password.length < 8) return setError("Password must be at least 8 characters.");
    setBusy(true);
    try {
      const { user } = isSignup ? await signUp(name, email, password) : await signIn(email, password);
      setUser(user);
      setPassword("");
      closeAuth();
      toast(isSignup ? `Welcome, ${user.name}. Your bills will now be saved.` : `Signed in as ${user.name}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && closeAuth()}>
      <div className="modal card" role="dialog" aria-modal="true" aria-labelledby="auth-title">
        <button className="icon-btn modal-close" onClick={closeAuth} aria-label="Close"><Close /></button>
        <span className="brand-mark"><Bolt /></span>
        <h2 id="auth-title">{isSignup ? "Create your account" : "Welcome back"}</h2>
        <p className="muted">
          {isSignup ? "Save every bill you analyse and see your history in one place." : "Sign in to see your saved bills."}
        </p>

        <div className="auth-switch" role="tablist">
          <button role="tab" aria-selected={!isSignup} onClick={() => openAuth("signin")}>Sign in</button>
          <button role="tab" aria-selected={isSignup} onClick={() => openAuth("signup")}>Create account</button>
        </div>

        <form className="auth-form" onSubmit={submit} noValidate>
          {isSignup && (
            <label>
              <span>Name</span>
              <input ref={first} value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" required maxLength={80} />
            </label>
          )}
          <label>
            <span>Email</span>
            <input ref={isSignup ? undefined : first} type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              autoComplete="email" required maxLength={200} />
          </label>
          <label>
            <span>Password</span>
            <div className="pw">
              <input type={show ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)}
                autoComplete={isSignup ? "new-password" : "current-password"} required minLength={isSignup ? 8 : 1} maxLength={200} />
              <button type="button" className="icon-btn" onClick={() => setShow((s) => !s)} aria-label={show ? "Hide password" : "Show password"}>
                <Eye />
              </button>
            </div>
            {isSignup && <small className="muted">At least 8 characters.</small>}
          </label>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="btn primary lg" disabled={busy || !email || !password || (isSignup && !name.trim())}>
            {busy ? "Please wait…" : isSignup ? "Create account" : "Sign in"}
          </button>
        </form>
        <p className="muted small center">You can also use Billsight without an account. Bills are then kept only in this browser.</p>
      </div>
    </div>
  );
}
