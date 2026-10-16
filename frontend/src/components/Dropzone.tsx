import { useRef, useState, type DragEvent } from "react";
import { Upload } from "./Icons";
import { toast } from "../toast";

interface Props {
  multiple?: boolean;
  onFiles: (files: File[]) => void;
  title: string;
  hint: string;
  compact?: boolean;
}

export const ACCEPT = ".png,.jpg,.jpeg,.webp,.pdf,image/png,image/jpeg,image/webp,application/pdf";
const OK_EXT = /\.(png|jpe?g|webp|pdf)$/i;
const MAX = 15 * 1024 * 1024;

export function pickValid(list: FileList | File[] | null): File[] {
  const files = Array.from(list ?? []);
  const good = files.filter((f) => OK_EXT.test(f.name) || /^image\/(png|jpeg|webp)$|^application\/pdf$/.test(f.type));
  const small = good.filter((f) => f.size <= MAX);
  if (files.length && !good.length) toast("Use a PNG, JPG, WEBP or PDF file.", "error");
  else if (good.length > small.length) toast("Files over 15 MB were skipped.", "error");
  return small;
}

export default function Dropzone({ multiple = false, onFiles, title, hint, compact = false }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  const take = (list: FileList | null) => {
    const files = pickValid(list);
    if (files.length) onFiles(multiple ? files : files.slice(0, 1));
  };

  const picker = (
    <input
      ref={input}
      type="file"
      accept={ACCEPT}
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
        {multiple ? "Choose files" : "Choose file"}
      </button>
      {picker}
    </div>
  );
}
