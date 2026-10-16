import { useRef, useState, type DragEvent } from "react";
import { Upload } from "./Icons";

interface Props {
  multiple?: boolean;
  onFiles: (files: File[]) => void;
  title: string;
  hint: string;
  compact?: boolean;
}

const ACCEPT = ["image/png", "image/jpeg", "image/webp"];

export default function Dropzone({ multiple = false, onFiles, title, hint, compact = false }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  const take = (list: FileList | null) => {
    const files = Array.from(list ?? []).filter((f) => ACCEPT.includes(f.type));
    if (files.length) onFiles(multiple ? files : files.slice(0, 1));
  };

  const picker = (
    <input
      ref={input}
      type="file"
      accept={ACCEPT.join(",")}
      multiple={multiple}
      hidden
      onChange={(e) => { take(e.target.files); e.target.value = ""; }}
    />
  );

  if (compact) {
    return (
      <>
        <button className="btn primary" onClick={() => input.current?.click()}><Upload /> New bill</button>
        {picker}
      </>
    );
  }

  return (
    <div
      className={`dropzone${over ? " over" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e: DragEvent) => { e.preventDefault(); setOver(false); take(e.dataTransfer.files); }}
    >
      <span className="dz-icon"><Upload /></span>
      <div className="dz-text">
        <p className="dz-title">{title}</p>
        <p className="dz-hint">{hint}</p>
      </div>
      <button className="btn primary" onClick={() => input.current?.click()}>
        {multiple ? "Choose images" : "Choose image"}
      </button>
      {picker}
    </div>
  );
}
