import type { Analysis } from "./types";

const KEY = "billsight-recent";
const MAX = 6;

export interface RecentBill { savedAt: string; data: Analysis }

export function loadRecent(): RecentBill[] {
  try {
    const raw = localStorage.getItem(KEY);
    const list = raw ? (JSON.parse(raw) as RecentBill[]) : [];
    return Array.isArray(list) ? list.filter((r) => r?.data?.bill) : [];
  } catch {
    return [];
  }
}

export function saveRecent(data: Analysis) {
  try {
    const rest = loadRecent().filter((r) => r.data.image_hash !== data.image_hash);
    const list = [{ savedAt: new Date().toISOString(), data }, ...rest].slice(0, MAX);
    localStorage.setItem(KEY, JSON.stringify(list));
  } catch { /* storage full or blocked: recent list is a convenience only */ }
}

export function clearRecent() {
  try { localStorage.removeItem(KEY); } catch { /* ignore */ }
}
