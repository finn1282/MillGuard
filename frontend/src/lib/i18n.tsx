import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type Lang = "en" | "ms";

// UI chrome only. Everything data-related comes from the API's _en/_ms fields.
const S = {
  mill: ["Mill", "Kilang"],
  machine: ["Machine", "Mesin"],
  impact: ["Impact", "Impak"],
  how: ["How it works", "Cara ia berfungsi"],
  sample: ["Sample data", "Data contoh"],
  play: ["Play replay", "Main ulang tayang"],
  pause: ["Pause replay", "Jeda ulang tayang"],
  replayClock: ["replay clock", "jam ulang tayang"],
  day: ["Day shift", "Syif siang"],
  night: ["Night shift", "Syif malam"],
  language: ["Language", "Bahasa"],
  bookmarks: ["Demo moments", "Detik demo"],
  back1h: ["One hour back", "Satu jam ke belakang"],
  fwd1h: ["One hour forward", "Satu jam ke hadapan"],
  loading: ["Loading…", "Memuatkan…"],
  error: ["Could not load this.", "Tidak dapat memuatkan."],
  retry: ["Try again", "Cuba lagi"],
  empty: ["Nothing to show here.", "Tiada apa untuk dipaparkan."],
  act: ["Act now", "Bertindak sekarang"],
  watch: ["Watch", "Pantau"],
  ok: ["Normal", "Normal"],
  notMonitored: ["Not monitored", "Tidak dipantau"],
  sendPhone: ["Send to phone", "Hantar ke telefon"],
  sending: ["Sending…", "Menghantar…"],
  sentTo: ["Sent to {n} phones", "Dihantar ke {n} telefon"],
  sendFailed: ["Not sent", "Tidak dihantar"],
} as const;

export type Key = keyof typeof S;

interface Ctx {
  lang: Lang; setLang: (l: Lang) => void;
  t: (k: Key, vars?: Record<string, string | number>) => string;
  pick: (o: object, base: string) => string;
}

const LangCtx = createContext<Ctx>(null!);

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>("en");
  useEffect(() => { document.documentElement.lang = lang; }, [lang]);
  const t: Ctx["t"] = (k, vars) => {
    let s: string = S[k][lang === "ms" ? 1 : 0];
    for (const [n, v] of Object.entries(vars ?? {})) s = s.replace(`{${n}}`, String(v));
    return s;
  };
  // pick(action, "headline") -> action.headline_en | action.headline_ms
  const pick: Ctx["pick"] = (o, base) => String((o as Record<string, unknown>)[`${base}_${lang}`] ?? "");
  return <LangCtx.Provider value={{ lang, setLang, t, pick }}>{children}</LangCtx.Provider>;
}

export const useLang = () => useContext(LangCtx);
