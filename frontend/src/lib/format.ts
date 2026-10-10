import type { Lang } from "./i18n";

const TZ = "Asia/Kuala_Lumpur";
const loc = (l: Lang) => (l === "ms" ? "ms-MY" : "en-GB");

export const rm = (n: number) => `RM${Math.round(n).toLocaleString("en-MY")}`;
export const rmMillions = (n: number) => `RM${(n / 1e6).toFixed(2)}m`;
export const pct = (n: number) => (n >= 95 ? ">95%" : `${Math.round(n)}%`);
export const num = (n: number, d = 0) => n.toLocaleString("en-MY", { maximumFractionDigits: d });

function parts(iso: string, l: Lang, o: Intl.DateTimeFormatOptions) {
  return new Intl.DateTimeFormat(loc(l), { timeZone: TZ, ...o }).format(new Date(iso));
}

export const clock = (iso: string, l: Lang) =>
  `${parts(iso, l, { weekday: "short", day: "2-digit", month: "short" })} · ${hhmm(iso)}`.replace(/,/g, "").toUpperCase();
export const hhmm = (iso: string) => parts(iso, "en", { hour: "2-digit", minute: "2-digit", hour12: false });
export const dayMonth = (iso: string, l: Lang) => parts(iso, l, { day: "2-digit", month: "short" }).toUpperCase();
export const monthShort = (iso: string, l: Lang) => parts(iso, l, { month: "short" });

// Replay times are MYT (+08:00); keep that offset when stepping the clock.
export function addHours(iso: string, h: number): string {
  const d = new Date(new Date(iso).getTime() + h * 3600e3 + 8 * 3600e3);
  return d.toISOString().slice(0, 19) + "+08:00";
}
