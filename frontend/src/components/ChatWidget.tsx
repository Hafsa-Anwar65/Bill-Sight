import { useEffect, useState } from "react";
import type { Bill } from "../types";
import AskBox from "./AskBox";
import { Chat, Close } from "./Icons";

export default function ChatWidget({ bill }: { bill: Bill }) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const close = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, []);

  return (
    <>
      {open && (
        <div className="chat" role="dialog" aria-label="Ask about this bill">
          <div className="chat-head">
            <span className="chat-avatar"><Chat /></span><div><p>Ask Billsight</p><p className="muted small">Answers use only this bill</p></div>
            <button className="icon-btn" onClick={() => setOpen(false)} aria-label="Close"><Close /></button>
          </div>
          <AskBox bill={bill} />
        </div>
      )}
      <button className="chat-fab" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        <Chat /> {open ? "Close" : "Ask Billsight"}
      </button>
    </>
  );
}
