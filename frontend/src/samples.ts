import { BASE } from "./env";
import type { Analysis } from "./types";

export interface Sample { slug: string; provider: string | null; bill_month: string | null; payable: number | null; units: number | null }

export async function loadSamples(): Promise<Sample[]> {
  try {
    const res = await fetch(`${BASE}demo/index.json`);
    return res.ok ? ((await res.json()) as Sample[]) : [];
  } catch {
    return [];
  }
}

export async function loadSample(slug: string): Promise<Analysis> {
  const res = await fetch(`${BASE}demo/${slug}.json`);
  if (!res.ok) throw new Error("The sample bill could not be loaded.");
  return (await res.json()) as Analysis;
}
