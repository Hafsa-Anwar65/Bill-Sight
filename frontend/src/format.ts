const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function rs(x: number | null | undefined, decimals?: number): string {
  if (x == null) return "—";
  const d = decimals ?? (Number.isInteger(Math.round(x * 100) / 100) ? 0 : 2);
  return `Rs ${x.toLocaleString("en-PK", { minimumFractionDigits: d, maximumFractionDigits: d })}`;
}

export function num(x: number | null | undefined, digits = 0): string {
  return x == null ? "—" : x.toLocaleString("en-PK", { maximumFractionDigits: digits });
}

export function monthLabel(m: string | null, long = false): string {
  if (!m) return "—";
  const [y, mo] = m.split("-").map(Number);
  const name = long
    ? new Date(y, mo - 1, 1).toLocaleString("en-GB", { month: "long" })
    : MONTHS[mo - 1];
  return long ? `${name} ${y}` : `${name} ${String(y).slice(2)}`;
}

export function dayLabel(iso: string | null): string {
  if (!iso) return "—";
  const [y, m, d] = iso.split("-").map(Number);
  return `${d} ${MONTHS[m - 1]} ${y}`;
}

export const TYPE_LABEL: Record<string, string> = {
  energy: "Energy",
  fixed: "Fixed charge",
  fpa: "Fuel adjustment",
  quarterly_adjustment: "Quarterly adjustment",
  surcharge: "Surcharge",
  meter_rent: "Meter rent",
  subsidy: "Subsidy",
  other: "Other",
  gst: "Sales tax",
  electricity_duty: "Electricity duty",
  income_tax: "Income tax",
  municipal_tax: "Municipal tax",
  other_tax: "Taxes",
};

export function download(name: string, text: string, type = "text/csv;charset=utf-8") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = Object.assign(document.createElement("a"), { href: url, download: name });
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const area = Object.assign(document.createElement("textarea"), { value: text });
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand("copy");
    area.remove();
    return ok;
  }
}

export const isPdf = (f: File) => f.type === "application/pdf" || /\.pdf$/i.test(f.name);
