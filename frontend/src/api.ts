import type { Analysis, Bill, Health } from "./types";

const OFFLINE = "Can't reach the Billsight server. Start it with: uvicorn app.api:app --port 8000";

function messageFrom(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return "Some of the request was invalid. Please try again.";
  if (status === 413) return "The file is larger than 15 MB.";
  if (status >= 500) return "The server had a problem reading this bill. Please try again.";
  return `Request failed (${status}).`;
}

async function request<T>(url: string, init: RequestInit = {}, timeoutMs = 120_000): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  let res: Response;
  try {
    res = await fetch(url, { ...init, signal: ctrl.signal });
  } catch (e) {
    throw new Error((e as Error).name === "AbortError" ? "This is taking too long. Check your internet and try again." : OFFLINE);
  } finally {
    clearTimeout(timer);
  }
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(messageFrom(body, res.status));
  return body as T;
}

export const getHealth = () => request<Health>("/api/health", {}, 8_000);

export function analyzeBill(file: File, useCache = true): Promise<Analysis> {
  const form = new FormData();
  form.append("file", file);
  return request<Analysis>(`/api/analyze?use_cache=${useCache}`, { method: "POST", body: form }, 180_000);
}

const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const askQuestion = (bill: Bill, question: string) =>
  request<{ answer: string }>("/api/ask", json({ bill, question }), 60_000);

export const exportCsv = (items: { bill_id: string; bill: Bill | null }[]) =>
  request<{ level1_csv: string; level2_csv: string }>("/api/export", json({ items }));
