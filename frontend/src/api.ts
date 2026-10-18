import type { Analysis, Bill, Health } from "./types";
import { DEMO_MESSAGE, STATIC_DEMO } from "./env";

const OFFLINE = "Can't reach the Billsight server. Start it with: uvicorn app.api:app --port 8000";

function messageFrom(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const field = String((detail[0] as { loc?: unknown[] })?.loc?.slice(-1)[0] ?? "");
    if (field === "password") return "Password must be at least 8 characters.";
    if (field === "email") return "Enter a valid email address.";
    if (field === "name") return "Enter your name.";
    return "Some of the details are invalid. Please check and try again.";
  }
  if (status === 413) return "The file is larger than 15 MB.";
  if (status >= 500) return "The server had a problem reading this bill. Please try again.";
  return `Request failed (${status}).`;
}

async function request<T>(url: string, init: RequestInit = {}, timeoutMs = 120_000): Promise<T> {
  if (STATIC_DEMO) throw new Error(DEMO_MESSAGE);
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

// ---------- accounts ----------
export interface User { id: number; name: string; email: string }
export interface SavedBill {
  id: number; bill_id: string; provider: string | null; bill_month: string | null;
  units: number | null; payable: number | null; saved_at: string;
}

export const getMe = () => request<{ user: User | null }>("/api/auth/me", {}, 8_000);
export const signUp = (name: string, email: string, password: string) =>
  request<{ user: User }>("/api/auth/signup", json({ name, email, password }));
export const signIn = (email: string, password: string) =>
  request<{ user: User }>("/api/auth/login", json({ email, password }));
export const signOut = () => request<{ ok: boolean }>("/api/auth/logout", { method: "POST" });

export const listBills = () => request<{ bills: SavedBill[] }>("/api/bills");
export const getSavedBill = (id: number) => request<Analysis & { saved_id: number }>(`/api/bills/${id}`);
export const deleteBill = (id: number) => request<{ ok: boolean }>(`/api/bills/${id}`, { method: "DELETE" });
