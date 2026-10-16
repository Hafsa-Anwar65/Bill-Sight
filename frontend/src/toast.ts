export type ToastKind = "ok" | "error";
export interface ToastMsg { id: number; text: string; kind: ToastKind }

let next = 1;
export function toast(text: string, kind: ToastKind = "ok") {
  window.dispatchEvent(new CustomEvent<ToastMsg>("billsight-toast", { detail: { id: next++, text, kind } }));
}
