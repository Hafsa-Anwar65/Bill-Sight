import type { Answer } from "../types";
import { copyText } from "../format";
import { toast } from "../toast";
import { Copy } from "./Icons";

export default function Answers({ answers }: { answers: Answer[] }) {
  const copy = async (text: string, what: string) => {
    const ok = await copyText(text);
    toast(ok ? `${what} copied` : "Could not copy to the clipboard", ok ? "ok" : "error");
  };
  const all = answers.map((a) => `${a.id}. ${a.question}\n${a.answer}`).join("\n\n");

  return (
    <section className="card pad">
      <div className="panel-head row">
        <div>
          <h3>Your bill, answered</h3>
          <p className="muted small">Calculated from the bill's numbers, not guessed by AI.</p>
        </div>
        <button className="btn ghost sm" onClick={() => copy(all, "All answers")}><Copy /> Copy all</button>
      </div>
      <ol className="answers">
        {answers.map((a) => (
          <li key={a.id}>
            <span className="qid">{a.id}</span>
            <div>
              <p className="q">{a.question}</p>
              <p className="a">{a.answer}</p>
            </div>
            <button className="icon-btn copy" onClick={() => copy(a.answer, a.id)} aria-label={`Copy answer ${a.id}`} title="Copy answer">
              <Copy />
            </button>
          </li>
        ))}
      </ol>
    </section>
  );
}
