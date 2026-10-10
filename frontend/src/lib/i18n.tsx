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
  // machine page
  backToMill: ["← Back to the mill", "← Kembali ke kilang"],
  deadline: ["Deadline", "Tarikh akhir"],
  nothingTonight: ["Nothing to do tonight", "Tiada tindakan malam ini"],
  notAlertYet: ["Watching, not an alert yet", "Dipantau, belum amaran"],
  stationPress: ["Pressing station", "Stesen penekanan"],
  stationBoiler: ["Boiler house · whole-mill risk", "Rumah dandang · risiko seluruh kilang"],
  ifNotFixed: ["If not fixed {when}: {pct} chance it fails {window}", "Jika tidak dibaiki {when}: {pct} kemungkinan rosak {window}"],
  atStop: ["at {label}", "pada {label}"],
  chanceOnly: ["{pct} chance it fails {window}", "{pct} kemungkinan rosak {window}"],
  allNormal: ["All signals normal", "Semua isyarat normal"],
  expectedLoss: ["Expected loss if you skip it", "Jangkaan kerugian jika dilangkau"],
  mathsLine: ["{pct} × {rm} breakdown", "{pct} × {rm} kerosakan"],
  mathsLineMill: ["{pct} × {rm} whole-mill stop", "{pct} × {rm} henti seluruh kilang"],
  whyFirst: ["Why first:", "Kenapa dahulu:"],
  whatsWrong: ["What's wrong", "Apa yang rosak"],
  whatWeChecked: ["What we checked", "Apa yang kami semak"],
  whatToDo: ["What to do", "Apa yang perlu dibuat"],
  diagnosis: ["Diagnosis", "Diagnosis"],
  confident: ["confident", "yakin"],
  lessLikely: ["Less likely:", "Kurang mungkin:"],
  fingerprint: ["Fault fingerprint", "Cap jari kerosakan"],
  nOfM: ["{n} of {m} match", "{n} daripada {m} sepadan"],
  usualSign: ["Usual sign", "Tanda biasa"],
  seenNow: ["Seen now", "Dilihat sekarang"],
  match: ["Match", "Padan"],
  yes: ["Yes", "Ya"],
  no: ["No", "Tidak"],
  notYet: ["Not yet", "Belum lagi"],
  early: ["Early pattern: only {n} of {m} usual signs so far. Check during the next stop.", "Corak awal: hanya {n} daripada {m} tanda biasa setakat ini. Semak semasa hentian seterusnya."],
  exp_up: ["rises", "naik"],
  exp_down: ["falls", "turun"],
  exp_unstable: ["swings", "berayun"],
  exp_spike: ["spikes", "melonjak"],
  exp_steady: ["stays steady", "kekal stabil"],
  evidence: ["Evidence · last 7 days", "Bukti · 7 hari lepas"],
  signals7d: ["Signals · last 7 days", "Isyarat · 7 hari lepas"],
  limit: ["limit", "had"],
  history: ["History on this machine", "Sejarah mesin ini"],
  noHistory: ["No breakdowns logged in the last 12 months.", "Tiada kerosakan direkodkan dalam 12 bulan lepas."],
  predicted: ["Predicted", "Diramal"],
  missed: ["Missed", "Terlepas"],
  learnAbout: ["Learn about {name} →", "Ketahui tentang {name} →"],
  fixNowMinus: ["− Fix now", "− Baiki sekarang"],
  fixAtStopMinus: ["− Fix at the planned stop", "− Baiki semasa hentian terancang"],
  youProtect: ["= You protect", "= Anda lindungi"],
  keepWatching: ["Keep watching", "Terus pantau"],
  costToFix: ["Cost to stop and fix", "Kos untuk henti dan baiki"],
  waitingCheaper: ["Waiting is cheaper by", "Menunggu lebih murah sebanyak"],
  actingSaves: ["Acting now would save", "Bertindak sekarang menjimatkan"],
  watchNote: ["MillGuard checks {name} every hour and raises a card only when a warning holds for several hours.", "MillGuard menyemak {name} setiap jam dan hanya menaikkan kad apabila amaran berterusan beberapa jam."],
  nothingKeepRunning: ["Nothing tonight. Keep running.", "Tiada apa malam ini. Teruskan operasi."],
  fixPlan: ["Fix plan", "Pelan pembaikan"],
  crewMeta: ["Crew {crew} · about {h} hours", "Kru {crew} · kira-kira {h} jam"],
  stop_none: ["no stop needed", "tiada hentian diperlukan"],
  stop_machine: ["needs machine stop", "perlu hentikan mesin"],
  stop_whole_mill: ["needs whole-mill stop", "perlu hentikan seluruh kilang"],
  noLostProd: ["No lost production", "Tiada kehilangan pengeluaran"],
  lostProd: ["Production is lost while it is stopped", "Pengeluaran hilang semasa ia dihentikan"],
  parts: ["Parts", "Alat ganti"],
  fixNow: ["Fix now", "Baiki sekarang"],
  schedule: ["Schedule", "Jadualkan"],
  fixNowBy: ["Fix now: {label}", "Baiki sekarang: {label}"],
  scheduleFor: ["Schedule for {label}", "Jadualkan untuk {label}"],
  useful: ["Was this useful?", "Adakah ini berguna?"],
  usefulYes: ["Useful", "Berguna"],
  usefulNo: ["Not useful", "Tidak berguna"],
  recorded: ["Recorded", "Direkodkan"],
  lastService: ["Last service", "Servis terakhir"],
  hoursAgo: ["{h} hours ago", "{h} jam lalu"],
  machines: ["Machines", "Mesin"],
  // mill page
  tonight: ["Tonight", "Malam ini"],
  thisShift: ["This shift", "Syif ini"],
  needYouOne: ["1 machine needs you", "1 mesin perlukan anda"],
  needYouMany: ["{n} machines need you", "{n} mesin perlukan anda"],
  nothingNeedsNight: ["Nothing needs you tonight", "Tiada apa perlukan anda malam ini"],
  nothingNeedsDay: ["Nothing needs you this shift", "Tiada apa perlukan anda syif ini"],
  alsoCounts: ["Also: {w} being watched · {s} weak signals ignored", "Juga: {w} dipantau · {s} isyarat lemah diabaikan"],
  counts: ["{w} being watched · {s} weak signals ignored", "{w} dipantau · {s} isyarat lemah diabaikan"],
  protectedIfAct: ["Protected if you act", "Dilindungi jika anda bertindak"],
  worthActing: ["Worth acting on", "Berbaloi untuk bertindak"],
  needsYouRanked: ["Needs you · most ringgit first", "Perlukan anda · ringgit terbanyak dahulu"],
  beingWatched: ["Being watched", "Sedang dipantau"],
  watchedNote: ["You'll get a card if it needs you.", "Anda akan menerima kad jika ia perlukan anda."],
  ignoredTitle: ["{s} weak signals ignored", "{s} isyarat lemah diabaikan"],
  ignoredBody: ["Too small or too short to be worth anyone's time. Keeping these quiet is how MillGuard avoids false alarms.", "Terlalu kecil atau terlalu singkat untuk diberi perhatian. Mendiamkan isyarat ini ialah cara MillGuard mengelakkan amaran palsu."],
  millOrder: ["The mill, in process order", "Kilang, mengikut urutan proses"],
  flowsLR: ["Fruit flows left to right", "Buah mengalir dari kiri ke kanan"],
  steamAll: ["Steam to every station", "Stim ke setiap stesen"],
  boilerHouse: ["Boiler house · steam for every station", "Rumah dandang · stim untuk setiap stesen"],
  st_ramp: ["Ramp", "Ramp"],
  st_sterilizer: ["Sterilizer", "Pensteril"],
  st_thresher: ["Thresher", "Pengirik"],
  st_digesters: ["Digesters", "Pencerna"],
  st_clarification: ["Clarification", "Penjernihan"],
  noMachines: ["No machine data for this time.", "Tiada data mesin untuk masa ini."],
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
