import { useSyncExternalStore } from "react";
import type {
  AdviceOut, Assumption, AssetDetail, Backtest, Brief, FaultGuide, FeedbackIn, FeedbackOut,
  IngestOut, Line, LiveSession, LiveStatus, Marker, Meta, NotifyOut, NotifyStatus, ReadingIn, Robustness, Scenario, UploadOut,
} from "./types";

// API base: empty = same origin (/api). ?api=<url> overrides it and is remembered in this browser; ?api=reset clears it.
const BASE_KEY = "mg.api";
function apiBase(): { base: string; override: boolean } {
  const env = String(import.meta.env.VITE_API_URL ?? "");
  const url = new URL(location.href);
  const q = url.searchParams.get("api");
  let saved: string | null = null;
  try {
    if (q === "reset") localStorage.removeItem(BASE_KEY);
    else if (q) localStorage.setItem(BASE_KEY, q);
    saved = localStorage.getItem(BASE_KEY);
  } catch { /* storage blocked */ }
  if (q !== null) { url.searchParams.delete("api"); history.replaceState(history.state, "", url); }
  const pick = q && q !== "reset" ? q : saved;
  return { base: (pick ?? env).replace(/\/+$/, "").replace(/\/api$/, ""), override: !!pick };
}
const { base: API, override } = apiBase();

// Live binding: becomes true when the startup check gives up on the server (see connect).
// An ?api= override means "talk to that server", even in a fixture build.
export let USE_FIXTURES = import.meta.env.VITE_USE_FIXTURES === "true" && !override;
let offline = false;
export const isOffline = () => offline;
export const isSample = () => USE_FIXTURES;

// Startup: GET /api/health (or /api/meta before health exists), 6 s per try, retried for 30 s to cover a cold start.
// Still nothing: run on the bundled sample data.
export async function connect(): Promise<void> {
  if (USE_FIXTURES) return;
  const end = Date.now() + 30_000;
  const ping = async (path: string) => {
    const r = await fetch(`${API}/api${path}`, { cache: "no-store", signal: AbortSignal.timeout(Math.min(6000, Math.max(1000, end - Date.now()))) });
    // An HTML 200 is a static host answering for a missing API, not the server.
    return r.ok && (r.headers.get("content-type") ?? "").includes("json") ? "up" : r.status === 404 ? "missing" : "down";
  };
  for (;;) {
    try {
      let s = await ping("/health");
      if (s === "missing") s = await ping("/meta");
      if (s === "up") return;
    } catch { /* timeout or no network */ }
    if (Date.now() + 2000 >= end) break;
    await new Promise((r) => setTimeout(r, 2000));
  }
  USE_FIXTURES = true;
  offline = true;
}

const files = import.meta.glob(["../../../contracts/fixtures/*.json", "../../../contracts/fixtures/backtest_grid/*.json"],
  { import: "default" }) as Record<string, () => Promise<unknown>>;

async function fixture<T>(name: string): Promise<T> {
  const key = Object.keys(files).find((k) => k.endsWith(`/${name}.json`));
  if (!key) throw new Error(`No fixture ${name}`);
  return (await files[key]()) as T;
}

// contracts/README.md: whole-mill = no suffix, act-now = _act, quiet = _quiet; match on the date of `at`.
async function suffixFor(at?: string): Promise<string> {
  const marks = await fixture<Record<string, string>>("bookmarks");
  const day = at?.slice(0, 10);
  const hit = Object.entries(marks).find(([, t]) => t.slice(0, 10) === day)?.[0];
  return hit === "act" ? "_act" : hit === "quiet" ? "_quiet" : "";
}

async function variant(name: string, at?: string): Promise<unknown> {
  const suffix = await suffixFor(at);
  return fixture(name + suffix).catch(() => fixture(name));
}

export class OfflineUnavailable extends Error {}

// Fixture advice: the backend's advice_<asset>[_act|_quiet]_<lang> file, else unavailable offline.
async function fixtureAdvice(asset_id: string, at: string, lang: "en" | "ms"): Promise<AdviceOut> {
  const key = `${asset_id}${await suffixFor(at)}_${lang}`;
  return fixture<AdviceOut>(`advice_${key}`).catch(() => { throw new OfflineUnavailable(key); });
}

// Presenter key for write endpoints (v1.14). Session storage only: never in the URL or the build.
const KEY = "mg.demoKey";
export function demoKey(): string | null { try { return sessionStorage.getItem(KEY); } catch { return null; } }
export function setDemoKey(k: string) { try { sessionStorage.setItem(KEY, k); } catch { /* private mode */ } setKeyNeeded(false); }

// Set by any write call that comes back 401; the Machine page shows a "Presenter key needed" link while it is set.
let keyNeeded = false;
const keyListeners = new Set<() => void>();
function setKeyNeeded(v: boolean) { if (v !== keyNeeded) { keyNeeded = v; keyListeners.forEach((l) => l()); } }
export const useKeyNeeded = () => useSyncExternalStore((l) => { keyListeners.add(l); return () => keyListeners.delete(l); }, () => keyNeeded);

export class HttpError extends Error {
  constructor(public status: number, message: string) { super(message); }
}
async function fail(r: Response): Promise<never> {
  let detail = r.statusText;
  try { const j = await r.json(); if (typeof j.detail === "string") detail = j.detail; } catch { /* not JSON */ }
  throw new HttpError(r.status, `${r.status} ${detail}`);
}

const cache = new Map<string, Promise<unknown>>();
// A new live session serves different data for the same `at`: drop everything cached.
export const clearCache = () => cache.clear();

async function fresh<T>(path: string, params: Record<string, string | number> = {}): Promise<T> {
  const q = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]));
  const r = await fetch(`${API}/api${path}${q.size ? `?${q}` : ""}`, { cache: "no-store" });
  return r.ok ? r.json() : fail(r);
}

function get<T>(path: string, params: Record<string, string | number | undefined> = {}): Promise<T> {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== "") q.set(k, String(v));
  const url = `${API}/api${path}${q.size ? `?${q}` : ""}`;
  if (!cache.has(url)) {
    const p = fetch(url).then((r) => {
      if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
      return r.json();
    });
    p.catch(() => cache.delete(url));
    cache.set(url, p);
  }
  return cache.get(url) as Promise<T>;
}

async function post<T>(path: string, body?: unknown, timeoutMs?: number): Promise<T> {
  const headers: Record<string, string> = {};
  const key = demoKey();
  if (key) headers["X-Demo-Key"] = key;
  const form = body instanceof FormData;
  if (!form) headers["Content-Type"] = "application/json";
  const r = await fetch(`${API}/api${path}`, {
    method: "POST", headers, body: form ? body : JSON.stringify(body ?? {}),
    signal: timeoutMs ? AbortSignal.timeout(timeoutMs) : undefined,
  });
  if (r.status === 401) setKeyNeeded(true);
  return r.ok ? r.json() : fail(r);
}

export type GridAxes = { cpo_price: number[]; miss_cost_mult: number[]; alert_budget: number[]; inspection_accuracy: number[] };
const nearest = (xs: number[], v: number) => xs.reduce((a, b) => (Math.abs(b - v) < Math.abs(a - v) ? b : a));

// Offline sliders: snap to the nearest precomputed grid point (contracts/README.md).
async function gridBacktest(p: BacktestParams): Promise<Backtest> {
  const { axes } = await fixture<{ axes: GridAxes }>("backtest_grid/index");
  const v = (k: keyof GridAxes, d: number) => String(nearest(axes[k], p[k] ?? d));
  return fixture<Backtest>(`backtest_grid/cpo${v("cpo_price", 4292.5)}_miss${v("miss_cost_mult", 1)}_bud${v("alert_budget", 5)}_acc${v("inspection_accuracy", 0.5)}`);
}

export interface BacktestParams {
  cpo_price?: number; miss_cost_mult?: number; alert_budget?: number;
  inspection_accuracy?: number; compare?: "run_to_failure" | "fixed_interval" | "millguard_only";
}

export const api = {
  meta: () => (USE_FIXTURES ? fixture<Meta>("meta") : get<Meta>("/meta")),
  markers: () => (USE_FIXTURES ? fixture<Marker[]>("replay_markers") : get<Marker[]>("/replay/markers")),
  brief: (at: string) => (USE_FIXTURES ? (variant("brief", at) as Promise<Brief>) : get<Brief>("/brief", { at })),
  line: (at: string) => (USE_FIXTURES ? (variant("line", at) as Promise<Line>) : get<Line>("/line", { at })),
  asset: (id: string, at: string, window_h = 168) =>
    USE_FIXTURES ? (variant(`assets_${id}`, at) as Promise<AssetDetail>)
      : get<AssetDetail>(`/assets/${id}`, { at, window_h }),
  backtest: (p: BacktestParams = {}) =>
    USE_FIXTURES ? gridBacktest(p).catch(() => fixture<Backtest>("backtest")) : get<Backtest>("/backtest", { ...p }),
  gridAxes: () => (USE_FIXTURES ? fixture<{ axes: GridAxes }>("backtest_grid/index").then((i) => i.axes) : Promise.resolve(null)),
  assumptions: () => (USE_FIXTURES ? fixture<Assumption[]>("assumptions") : get<Assumption[]>("/assumptions")),
  robustness: () => (USE_FIXTURES ? fixture<Robustness>("robustness") : get<Robustness>("/robustness")),
  faults: () => (USE_FIXTURES ? fixture<FaultGuide[]>("faults") : get<FaultGuide[]>("/faults")),
  feedback: (body: FeedbackIn) =>
    USE_FIXTURES ? fixture<FeedbackOut>("feedback") : post<FeedbackOut>("/feedback", body),
  // v1.8: any failure means "disabled"; the button only shows when enabled.
  notifyStatus: (): Promise<NotifyStatus> =>
    (USE_FIXTURES ? fixture<NotifyStatus>("notify_status") : get<NotifyStatus>("/notify/status"))
      .catch(() => ({ enabled: false, channel: "", subscribers: 0 })),
  // The model can take up to 30 s plus one retry on the backend.
  advice: (asset_id: string, at: string, lang: "en" | "ms") =>
    USE_FIXTURES ? fixtureAdvice(asset_id, at, lang) : post<AdviceOut>("/advice", { asset_id, at, lang }, 75_000),
  // v1.14 gateway. Live endpoints are never cached; offline mode has no live backend.
  live: (): Promise<LiveStatus | null> => (USE_FIXTURES ? Promise.resolve(null) : fresh<LiveStatus>("/live")),
  scenarios: () => get<Scenario[]>("/scenarios"),
  scenarioHours: (id: string, from: string, n = 24) => fresh<ReadingIn[]>(`/scenarios/${id}/hours`, { from, n }),
  ingest: (rows: ReadingIn[]) => post<IngestOut>("/ingest", rows),
  liveStart: (scenario_id: string, start: string | undefined, speed_s_per_h: number) =>
    post<LiveSession>("/live/start", { scenario_id, start, speed_s_per_h }),
  liveStop: () => post<LiveStatus>("/live/stop"),
  upload: (file: File) => { const f = new FormData(); f.append("file", file); return post<UploadOut>("/upload", f, 60_000); },
  notify: (at: string, kind: "alert" | "brief" | "schedule" = "alert", action_id?: string) =>
    post<NotifyOut>("/notify", { at, kind, action_id }),
  // v1.13 Schedule: notify only, the backend records the feedback whether Telegram is on or off.
  // Backend unreachable: record the feedback directly. Sample data never sends, so it never claims to.
  schedule: async (at: string, action_id: string): Promise<{ sample: boolean; sent: number }> => {
    if (isSample()) return { sample: true, sent: 0 };
    try {
      const r = await api.notify(at, "schedule", action_id);
      return { sample: false, sent: r.ok ? r.sent : 0 };
    } catch (e) {
      if (e instanceof TypeError) api.feedback({ action_id, decision: "schedule_next_stop" }).catch(() => {});
      return { sample: false, sent: 0 };
    }
  },
};
