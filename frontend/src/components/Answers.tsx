import type { Answer } from "../types";

export default function Answers({ answers }: { answers: Answer[] }) {
  return (
    <section className="card pad">
      <div className="panel-head">
        <h3>Your bill, answered</h3>
        <p className="muted">Calculated from the bill's numbers, not guessed by AI.</p>
      </div>
      <ol className="answers">
        {answers.map((a) => (
          <li key={a.id}>
            <span className="qid">{a.id}</span>
            <div>
              <p className="q">{a.question}</p>
              <p className="a">{a.answer}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
