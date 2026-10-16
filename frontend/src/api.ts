import type { Analysis, Bill, Health } from "./types";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url, init);
  } catch {
    throw new Error("The server is not running. Start it with: uvicorn app.api:app --port 8000");
  }
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(body?.detail ?? `Request failed (${res.status}).`);
  return body as T;
}

export const getHealth = () => request<Health>("/api/health");

export function analyzeBill(file: File, useCache = true): Promise<Analysis> {
  const form = new FormData();
  form.append("file", file);
  return request<Analysis>(`/api/analyze?use_cache=${useCache}`, { method: "POST", body: form });
}

export const askQuestion = (bill: Bill, question: string) =>
  request<{ answer: string }>("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ bill, question }),
  });

export const exportCsv = (items: { bill_id: string; bill: Bill | null }[]) =>
  request<{ level1_csv: string; level2_csv: string }>("/api/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items }),
  });
