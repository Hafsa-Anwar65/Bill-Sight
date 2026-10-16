import { useEffect, useState } from "react";
import type { ToastMsg } from "../toast";
import { Alert, Check } from "./Icons";

export default function Toaster() {
  const [items, setItems] = useState<ToastMsg[]>([]);

  useEffect(() => {
    const on = (e: Event) => {
      const msg = (e as CustomEvent<ToastMsg>).detail;
      setItems((xs) => [...xs, msg]);
      setTimeout(() => setItems((xs) => xs.filter((x) => x.id !== msg.id)), 3200);
    };
    window.addEventListener("billsight-toast", on);
    return () => window.removeEventListener("billsight-toast", on);
  }, []);

  return (
    <div className="toaster" role="status" aria-live="polite">
      {items.map((t) => (
        <div key={t.id} className={`toast ${t.kind}`}>
          {t.kind === "ok" ? <Check /> : <Alert />}
          <span>{t.text}</span>
        </div>
      ))}
    </div>
  );
}
