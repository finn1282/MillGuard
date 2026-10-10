import type {
  Assumption, AssetDetail, Backtest, Brief, FaultGuide, FeedbackIn, FeedbackOut,
  Line, Marker, Meta, NotifyOut, NotifyStatus, Robustness,
} from "./types";

export const USE_FIXTURES = import.meta.env.VITE_USE_FIXTURES === "true";
const API = String(import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

const files = import.meta.glob(["../../../contracts/fixtures/*.json", "../../../contracts/fixtures/backtest_grid/*.json"],
  { import: "default" }) as Record<string, () => Promise<unknown>>;

async function fixture<T>(name: string): Promise<T> {
  const key = Object.keys(files).find((k) => k.endsWith(`/${name}.json`));
  if (!key) throw new Error(`No fixture ${name}`);
  return (await files[key]()) as T;
}

// contracts/README.md: whole-mill = no suffix, act-now = _act, quiet = _quiet; match on the date of `at`.
async function variant(name: string, at?: string): Promise<unknown> {
  const marks = await fixture<Record<string, string>>("bookmarks");
  const day = at?.slice(0, 10);
  const hit = Object.entries(marks).find(([, t]) => t.slice(0, 10) === day)?.[0];
  const suffix = hit === "act" ? "_act" : hit === "quiet" ? "_quiet" : "";
  return fixture(name + suffix).catch(() => fixture(name));
}

const cache = new Map<string, Promise<unknown>>();

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

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${API}/api${path}`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
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
  notify: (at: string, kind: "alert" | "brief" = "alert") => post<NotifyOut>("/notify", { at, kind }),
};
