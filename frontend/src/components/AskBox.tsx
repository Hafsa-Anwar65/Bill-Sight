import { useState, type FormEvent } from "react";
import { askQuestion } from "../api";
import type { Bill } from "../types";

const SUGGESTIONS = ["Why is my bill this high?", "Mera bill kitna kam ho sakta hai?", "What is the PHL surcharge?"];

interface Turn { q: string; a?: string; error?: string }

export default function AskBox({ bill }: { bill: Bill }) {
  const [text, setText] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);

  const ask = async (q: string) => {
    const question = q.trim();
    if (!question || busy) return;
    setText("");
    setBusy(true);
    setTurns((t) => [...t, { q: question }]);
    try {
      const { answer } = await askQuestion(bill, question);
      setTurns((t) => t.map((x, i) => (i === t.length - 1 ? { ...x, a: answer } : x)));
    } catch (e) {
      setTurns((t) => t.map((x, i) => (i === t.length - 1 ? { ...x, error: (e as Error).message } : x)));
    } finally {
      setBusy(false);
    }
  };

  const submit = (e: FormEvent) => { e.preventDefault(); ask(text); };

  return (
    <section className="askbox">
      {turns.length > 0 && (
        <div className="turns" aria-live="polite">
          {turns.map((t, i) => (
            <div key={i} className="turn">
              <p className="you">{t.q}</p>
              {t.a && <p className="bot">{t.a}</p>}
              {t.error && <p className="bot error">{t.error}</p>}
              {!t.a && !t.error && <p className="bot muted">Thinking…</p>}
            </div>
          ))}
        </div>
      )}
      <form className="ask" onSubmit={submit}>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. How much tax am I paying?"
          aria-label="Your question"
          maxLength={500}
        />
        <button className="btn primary" disabled={busy || !text.trim()}>Ask</button>
      </form>
      <div className="chips">
        {SUGGESTIONS.map((s) => (
          <button key={s} className="chip" onClick={() => ask(s)} disabled={busy}>{s}</button>
        ))}
      </div>
    </section>
  );
}
