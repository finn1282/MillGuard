import { useSyncExternalStore } from "react";
import { api, HttpError } from "./api";
import { addHours } from "./format";
import type { ReadingIn, SensorAlert } from "./types";

// The browser is the sensor gateway (v1.14): it fetches scenario hours and POSTs them to /api/ingest at its own pace.
// Module state, so the stream keeps going when the presenter switches pages in this tab. A hidden tab pauses it.

export type LogLine = { id: number; text: string; issue?: boolean };
export interface Gateway {
  running: boolean; scenario: string | null; speed: number; cursor: string | null;
  sent: number; log: LogLine[]; locked: boolean; error: string | null; hiddenPause: boolean;
}

let state: Gateway = { running: false, scenario: null, speed: 2, cursor: null, sent: 0, log: [], locked: false, error: null, hiddenPause: false };
const listeners = new Set<() => void>();
const set = (p: Partial<Gateway>) => { state = { ...state, ...p }; listeners.forEach((l) => l()); };
export const useGateway = () => useSyncExternalStore((l) => { listeners.add(l); return () => listeners.delete(l); }, () => state);

let timer: number | undefined;
let buffer: ReadingIn[][] = [];
let nextFrom: string | null = null;
let lineId = 0;
let gen = 0; // bumped on every start/stop, so a tick still awaiting the network cannot revive an old loop
const seenIssues = new Set<string>();

const fail = (e: unknown) => {
  stopLoop();
  if (e instanceof HttpError && e.status === 401) set({ locked: true, error: null });
  else set({ error: e instanceof Error ? e.message : String(e) });
};

function addLog(lines: LogLine[]) { set({ log: [...lines.reverse(), ...state.log].slice(0, 20) }); }

// One line per payload: asset, time and the first 4 readings.
function compact(r: ReadingIn): string {
  const vals = Object.entries(r.readings).filter(([, v]) => v != null).slice(0, 4);
  return JSON.stringify({ asset: r.asset_id, t: r.t.slice(5, 16).replace("T", " "), ...Object.fromEntries(vals) });
}

async function nextHour(): Promise<ReadingIn[] | null> {
  if (!buffer.length && state.scenario && nextFrom) {
    const rows = await api.scenarioHours(state.scenario, nextFrom, 24);
    const byT = new Map<string, ReadingIn[]>();
    for (const r of rows) byT.set(r.t, [...(byT.get(r.t) ?? []), r]);
    buffer = [...byT.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([, v]) => v);
    if (buffer.length) nextFrom = addHours(buffer[buffer.length - 1][0].t, 1);
  }
  return buffer.shift() ?? null;
}

async function tick(g = gen) {
  timer = undefined;
  if (!state.running || g !== gen) return;
  const t0 = performance.now();
  if (document.hidden) { set({ hiddenPause: true }); schedule(1000); return; }
  try {
    const hour = await nextHour();
    if (!state.running || g !== gen) return;
    if (!hour) { set({ running: false, error: "End of scenario data." }); return; }
    const out = await api.ingest(hour);
    if (g !== gen) return;
    const lines: LogLine[] = hour.map((r) => ({ id: ++lineId, text: compact(r) }));
    for (const s of out.sensor_issues as SensorAlert[]) {
      const k = `${s.asset_id}|${s.signal}|${s.kind}|${s.first_t}`;
      if (seenIssues.has(k)) continue;
      seenIssues.add(k);
      lines.push({ id: ++lineId, issue: true, text: JSON.stringify({ sensor_issue: s.kind, asset: s.asset_id, signal: s.signal, since: s.first_t.slice(5, 16).replace("T", " ") }) });
    }
    addLog(lines);
    set({ sent: state.sent + out.accepted, cursor: addHours(hour[0].t, 1), hiddenPause: false, error: null });
    schedule(state.speed * 1000 - (performance.now() - t0));
  } catch (e) { if (g === gen) fail(e); }
}

function schedule(ms: number) { if (state.running) timer = window.setTimeout(tick, Math.max(0, ms)); }
function stopLoop() { gen++; if (timer) clearTimeout(timer); timer = undefined; buffer = []; set({ running: false, hiddenPause: false }); }

function begin(scenario: string, from: string) {
  buffer = []; nextFrom = from; seenIssues.clear();
  set({ running: true, scenario, cursor: from, error: null, hiddenPause: false });
  tick();
}

export const gateway = {
  setSpeed: (speed: number) => set({ speed }),
  setScenario: (scenario: string) => { if (!state.running) set({ scenario }); },
  unlock: () => set({ locked: false }),
  async start(scenario: string, start: string | undefined) {
    stopLoop();
    try {
      const s = await api.liveStart(scenario, start, state.speed);
      set({ sent: 0, log: [] });
      begin(scenario, s.start_t);
    } catch (e) { fail(e); }
  },
  // A session is live but this tab is not sending (reload, other screen): carry on from the next hour.
  resume(scenario: string, liveAt: string) { begin(scenario, addHours(liveAt, 1)); },
  async stop() {
    stopLoop();
    try { await api.liveStop(); } catch (e) { fail(e); }
  },
};

document.addEventListener("visibilitychange", () => {
  if (!document.hidden && state.running && timer) { clearTimeout(timer); tick(); }
});
