import type { Bill } from "./types";

/** An all-day calendar event on the due date with a reminder the day before (.ics). */
export function dueDateIcs(bill: Bill, payable: string): string | null {
  if (!bill.due_date) return null;
  const d = bill.due_date.replace(/-/g, "");
  const next = new Date(`${bill.due_date}T00:00:00Z`);
  next.setUTCDate(next.getUTCDate() + 1);
  const end = next.toISOString().slice(0, 10).replace(/-/g, "");
  const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d+Z$/, "Z");
  const who = bill.provider === "KE" ? "K-Electric" : bill.provider ?? "Electricity";
  return [
    "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Billsight//EN", "CALSCALE:GREGORIAN",
    "BEGIN:VEVENT",
    `UID:${d}-${who.replace(/\W/g, "")}@billsight`,
    `DTSTAMP:${stamp}`,
    `DTSTART;VALUE=DATE:${d}`,
    `DTEND;VALUE=DATE:${end}`,
    `SUMMARY:Pay ${who} bill (${payable})`,
    "DESCRIPTION:Pay by today to avoid the late payment surcharge.",
    "BEGIN:VALARM", "TRIGGER:-P1D", "ACTION:DISPLAY", "DESCRIPTION:Electricity bill due tomorrow", "END:VALARM",
    "END:VEVENT", "END:VCALENDAR",
  ].join("\r\n");
}
