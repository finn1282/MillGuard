import { useEffect, useRef, useState } from "react";
import { AssumptionsDrawer } from "../components/AssumptionsDrawer";
import { IconPause, IconPlay } from "../components/Icons";
import { PageBar } from "../components/PageBar";
import { ErrorBox, Loading } from "../components/States";
import { api, USE_FIXTURES, type BacktestParams, type GridAxes } from "../lib/api";
import { useClock } from "../lib/clock";
import { monthShort, num, rmMillions } from "../lib/format";
import { useLang, type Key } from "../lib/i18n";
import type { Backtest, BacktestEvent, PolicyId, PolicyResult } from "../lib/types";
import { useApi } from "../lib/useApi";

type Compare = NonNullable<BacktestParams["compare"]>;
const BEFORE: Record<Compare, PolicyId> = { run_to_failure: "run_to_failure", fixed_interval: "fixed_interval", millguard_only: "millguard" };
const AFTER: PolicyId = "schedule_plus_millguard";

export function Impact() {
  const { meta } = useClock();
  const { t, lang } = useLang();
  // alert_budget is left to the API default; the UI shows the limit as a fixed line instead of a slider.
  const base = { cpo_price: meta?.mill.cpo_price_rm ?? 4292.5, miss_cost_mult: 1, inspection_accuracy: 0.5 };
  const [params, setParams] = useState(base);
  const [query, setQuery] = useState(base);
  const [compare, setCompare] = useState<Compare>("run_to_failure");
  const [drawer, setDrawer] = useState(false);

  // Debounce slider drags into one request.
  useEffect(() => { const id = setTimeout(() => setQuery(params), 250); return () => clearTimeout(id); }, [params]);
  const res = useApi(() => api.backtest({ ...query, compare }), [JSON.stringify(query), compare]);

  const r = meta?.replay;
  const sub = r ? t("replayYears", { from: monthShort(r.start, lang), to: monthShort(r.end, lang), year: r.end.slice(0, 4) }) : undefined;

  return (
    <>
      <PageBar title={meta?.mill.name ?? "MillGuard"} sub={sub} />
      {res.error && !res.data ? <ErrorBox error={res.error} retry={res.retry} /> : !res.data ? <Loading /> : (
        <div className="flex flex-wrap gap-3.5 lg:gap-6 items-start p-4 lg:px-10 lg:pt-7 lg:pb-14 max-w-[1400px]">
          <Main bt={res.data} compare={compare} setCompare={setCompare} loading={res.loading} openDrawer={() => setDrawer(true)} />
          <Sliders params={params} setParams={setParams} reset={() => setParams(base)} loading={res.loading} />
        </div>
      )}
      <AssumptionsDrawer open={drawer} onClose={() => setDrawer(false)} />
    </>
  );
}

function Main({ bt, compare, setCompare, loading, openDrawer }:
  { bt: Backtest; compare: Compare; setCompare: (c: Compare) => void; loading: boolean; openDrawer: () => void }) {
  const { t } = useLang();
  const pol = (id: PolicyId) => bt.policies.find((p) => p.id === id);
  const before = pol(BEFORE[compare]);
  const after = pol(AFTER);
  if (!before || !after) return <ErrorBox />;
  const saved = before.total_cost_rm - after.total_cost_rm;
  const fewer = before.breakdowns - after.breakdowns;

  return (
    <div className={`basis-[600px] grow-[999] min-w-0 flex flex-col gap-3.5 lg:gap-5 transition-opacity ${loading ? "opacity-70" : ""}`} aria-busy={loading}>
      <div className="flex flex-col lg:flex-row lg:justify-between lg:items-center gap-3 lg:gap-4 flex-wrap">
        <h1 className="m-0 text-[26px] lg:text-4xl font-extrabold">{t("isItWorth")}</h1>
        <div role="group" aria-label={t("compareWith")} className="flex flex-col lg:flex-row gap-1.5 lg:gap-0 lg:border lg:border-control-border lg:rounded lg:overflow-hidden lg:bg-card">
          <span className="text-sm lg:text-base text-muted font-semibold lg:font-normal lg:px-3 lg:flex lg:items-center">{t("compareWith")}</span>
          <div className="grid grid-cols-1 lg:flex border lg:border-0 border-control-border rounded lg:rounded-none overflow-hidden bg-card">
            {(Object.keys(BEFORE) as Compare[]).map((c, i) => (
              <button key={c} aria-pressed={compare === c} onClick={() => setCompare(c)}
                className={`min-h-[44px] px-3 lg:px-3.5 py-1.5 text-[15px] lg:text-base font-bold leading-tight ${i ? "border-t lg:border-t-0 lg:border-l border-rule" : ""}
                  ${compare === c ? "bg-brand text-white" : "bg-transparent text-ink"}`}>
                {t(`pol_${BEFORE[c]}` as Key)}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-brand text-white rounded p-5 lg:px-7 lg:py-[26px] flex flex-wrap items-baseline justify-between gap-x-8 gap-y-1.5 lg:gap-y-3">
        <div className="min-w-0">
          <div className="text-[15px] lg:text-lg text-db-label">{t(`savedVs_${compare}` as Key)}</div>
          <div className="font-num font-extrabold text-db-protect tracking-tight leading-none text-[46px] lg:text-[80px]">RM{num(saved)}</div>
        </div>
        <div className="text-[19px] lg:text-[26px] font-extrabold">
          {fewer > 0 ? t("fewerBreakdowns", { n: fewer }) : fewer < 0 ? t("moreBreakdowns", { n: -fewer }) : t("sameBreakdowns")}
        </div>
      </div>

      <div className="grid gap-3.5 lg:gap-4 grid-cols-[repeat(auto-fit,minmax(min(100%,320px),1fr))]">
        <PolicyCard p={before} label={t("before")} tone="loss" />
        <PolicyCard p={after} label={t("after")} tone="ok" />
      </div>

      <Strip bt={bt} before={before.id} after={after.id} />
      <button onClick={openDrawer} className="link-btn self-start">
        {t("seeSources")}
      </button>
    </div>
  );
}

function PolicyCard({ p, label, tone }: { p: PolicyResult; label: string; tone: "loss" | "ok" }) {
  const { t } = useLang();
  const stat = (k: Key, v: string) => (
    <div className="flex justify-between items-baseline gap-3 py-3 border-t border-rule-soft text-base lg:text-lg">
      <span>{t(k)}</span><strong className="font-num text-xl lg:text-[26px]">{v}</strong>
    </div>
  );
  return (
    <div className={`sec flex flex-col border-t-4 ${tone === "loss" ? "border-t-loss" : "border-t-ok"}`}>
      <p className="label">{label}</p>
      <h2 className="grow mt-1 lg:mt-1.5 mb-1.5 lg:mb-2.5 text-[19px] lg:text-2xl font-extrabold">{t(`pol_${p.id}` as Key)}</h2>
      <div className={`font-num font-extrabold tracking-tight text-[36px] lg:text-[52px] leading-tight mb-2 ${tone === "loss" ? "text-loss" : "text-ok"}`}>
        {rmMillions(p.total_cost_rm)} <span className="font-ui text-sm lg:text-lg font-semibold text-muted tracking-normal">{t("perYear")}</span>
      </div>
      {stat("breakdowns", num(p.breakdowns))}
      {stat("downtime", `${num(p.downtime_h)} h`)}
      {stat("falseAlarms", num(p.false_alarms))}
    </div>
  );
}

// Two lanes over the year; "Play the year" sweeps a cursor and the totals climb with it.
function Strip({ bt, before, after }: { bt: Backtest; before: PolicyId; after: PolicyId }) {
  const { t, lang } = useLang();
  const [p, setP] = useState(1);
  const [playing, setPlaying] = useState(false);
  const raf = useRef(0);
  const tl = bt.timeline;
  const t0 = new Date(tl[0].t).getTime();
  const t1 = new Date(tl[tl.length - 1].t).getTime() + 864e5;
  const pos = (iso: string) => (new Date(iso).getTime() - t0) / (t1 - t0);

  useEffect(() => {
    if (!playing) return;
    const start = performance.now() - p * 8000;
    const tick = (now: number) => {
      const v = Math.min(1, (now - start) / 8000);
      setP(v);
      if (v < 1) raf.current = requestAnimationFrame(tick); else setPlaying(false);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing]);

  const play = () => { if (!playing && p >= 1) setP(0); setPlaying(!playing); };
  const idx = Math.min(tl.length - 1, Math.floor(p * tl.length));
  const months = Array.from({ length: 12 }, (_, m) => monthShort(`${tl[0].t.slice(0, 4)}-${String(m + 1).padStart(2, "0")}-15T00:00:00+08:00`, lang));

  const lane = (id: PolicyId, tone: string) => {
    const ev = bt.events.filter((e) => e.policy === id);
    const c = (ty: BacktestEvent["type"]) => ev.filter((e) => e.type === ty).length;
    // Label + total, then the lane full width (long policy names never squeeze the lane).
    return (<div className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-3 gap-y-1.5 items-center">
      <span className="text-[15px] lg:text-[17px] font-bold">{t(`pol_${id}` as Key)}</span>
      <div role="img" aria-label={t("laneLabel", { b: c("breakdown"), p: c("planned_fix"), f: c("false_alarm") })}
        className="relative h-11 lg:h-14 bg-paper rounded-[4px] overflow-hidden col-span-2 row-start-2">
        {ev.filter((e) => pos(e.t) <= p).map((e, i) => {
          const left = `${(pos(e.t) * 100).toFixed(2)}%`;
          if (e.type === "breakdown") return <span key={i} style={{ left }} className="absolute top-2.5 lg:top-3.5 w-[3px] lg:w-[5px] h-6 lg:h-7 bg-act rounded-[1px]" />;
          if (e.type === "planned_fix") return <span key={i} style={{ left }} className="absolute top-[17px] lg:top-[22px] w-[9px] h-[9px] lg:w-3 lg:h-3 rounded-full bg-ok" />;
          return <span key={i} style={{ left }} className="absolute bottom-1 lg:bottom-1.5 w-[7px] h-[7px] rounded-full border-2 border-muted" />;
        })}
        <span className="absolute top-0 bottom-0 w-0.5 bg-ink" style={{ left: `${p * 100}%` }} aria-hidden />
      </div>
      <span className={`font-num font-extrabold text-right text-[17px] lg:text-2xl col-start-2 row-start-1 ${tone}`}>{rmMillions(tl[idx].cost[id])}</span>
    </div>);
  };

  const legend = (
    <div className="flex gap-3.5 lg:gap-4 items-center flex-wrap text-sm lg:text-base">
      <span className="flex items-center gap-1.5"><span className="w-[3px] lg:w-[5px] h-4 lg:h-[22px] bg-act rounded-[1px]" aria-hidden />{t("breakdown")}</span>
      <span className="flex items-center gap-1.5"><span className="w-[9px] h-[9px] lg:w-3 lg:h-3 rounded-full bg-ok" aria-hidden />{t("plannedFix")}</span>
      <span className="flex items-center gap-1.5"><span className="w-[7px] h-[7px] rounded-full border-2 border-muted" aria-hidden />{t("falseAlarm")}</span>
    </div>
  );

  return (
    <div className="sec flex flex-col gap-2.5 lg:gap-3.5">
      <div className="flex justify-between items-center gap-3 flex-wrap">
        <h2 className="m-0 text-lg lg:text-[22px] font-extrabold">{t("twelveMonths")}</h2>
        <div className="flex gap-4 items-center flex-wrap">
          <span className="hidden lg:flex">{legend}</span>
          <button onClick={play} className="btn btn-primary min-h-[44px] lg:min-h-[48px] text-sm lg:text-base inline-flex gap-2 items-center">
            {playing ? <IconPause size={14} /> : <IconPlay size={14} />}{t(playing ? "pauseYear" : "playYear")}
          </button>
        </div>
      </div>
      <div className="flex flex-col gap-3 lg:gap-4">
        {lane(before, "text-loss")}
        {lane(after, "text-ok")}
        <div className="grid grid-cols-12 text-[11px] lg:text-base text-muted">
          {months.map((m, i) => <span key={i}>{lang === "en" ? m.charAt(0) : m.slice(0, 3)}</span>)}
        </div>
      </div>
      <span className="lg:hidden">{legend}</span>
    </div>
  );
}

type Params = { cpo_price: number; miss_cost_mult: number; inspection_accuracy: number };

function Sliders({ params, setParams, reset, loading }:
  { params: Params; setParams: (p: Params) => void; reset: () => void; loading: boolean }) {
  const { t } = useLang();
  const grid = useApi(api.gridAxes, []).data as GridAxes | null | undefined;
  const limit = useApi(api.assumptions, []).data?.find((a) => a.key === "alerting.max_per_shift")?.value;
  const row = (k: keyof Params, label: Key, min: number, max: number, step: number, fmt: (v: number) => string) => {
    // Fixture mode: the slider moves along the grid's axis values only.
    const axis = grid?.[k];
    if (axis) {
      const i = axis.reduce((best, x, j) => (Math.abs(x - params[k]) < Math.abs(axis[best] - params[k]) ? j : best), 0);
      return (
        <div className="flex flex-col gap-2 py-3.5 lg:py-4 border-t border-rule-soft">
          <div className="flex justify-between gap-2">
            <label htmlFor={`s-${k}`} className="text-[15px] lg:text-[17px] font-bold">{t(label)}</label>
            <span className="font-num text-[15px] lg:text-[17px] font-bold">{fmt(axis[i])}</span>
          </div>
          <input id={`s-${k}`} type="range" min={0} max={axis.length - 1} step={1} value={i} aria-valuetext={fmt(axis[i])}
            onChange={(e) => setParams({ ...params, [k]: axis[Number(e.target.value)] })}
            className="w-full h-11 accent-[var(--brand)]" />
          <div className="flex justify-between text-sm lg:text-base text-muted">{axis.map((x) => <span key={x}>{fmt(x)}</span>)}</div>
        </div>
      );
    }
    return (
    <div className="flex flex-col gap-2 py-3.5 lg:py-4 border-t border-rule-soft">
      <div className="flex justify-between gap-2">
        <label htmlFor={`s-${k}`} className="text-[15px] lg:text-[17px] font-bold">{t(label)}</label>
        <span className="font-num text-[15px] lg:text-[17px] font-bold">{fmt(params[k])}</span>
      </div>
      <input id={`s-${k}`} type="range" min={min} max={max} step={step} value={params[k]}
        onChange={(e) => setParams({ ...params, [k]: Number(e.target.value) })}
        className="w-full h-11 accent-[var(--brand)] disabled:opacity-50" />
      <div className="flex justify-between text-sm lg:text-base text-muted"><span>{fmt(min)}</span><span>{fmt(max)}</span></div>
    </div>
    );
  };
  return (
    <aside aria-labelledby="wi" className="sec basis-[320px] grow lg:max-w-[380px] rounded-t-2xl lg:rounded shadow-[0_-8px_24px_var(--shadow)] lg:shadow-none">
      <div className="flex justify-between items-baseline gap-2">
        <h2 id="wi" className="m-0 text-[19px] lg:text-2xl font-extrabold">{t("whatIf")}</h2>
        {loading && <span role="status" className="text-sm text-muted">{t("updating")}</span>}
      </div>
      <p className="mt-1 mb-1.5 text-[15px] lg:text-base text-muted">{t(USE_FIXTURES ? "whatIfFixture" : "whatIfSub")}</p>
      {row("cpo_price", "cpoPrice", 3800, 5000, 10, (v) => `RM${v.toLocaleString("en-MY", { minimumFractionDigits: v % 1 ? 2 : 0 })}/t`)}
      {row("miss_cost_mult", "missCost", 0.5, 3, 0.1, (v) => `${v.toFixed(1)}×`)}
      {limit != null && (
        <p className="m-0 py-3.5 lg:py-4 border-t border-rule-soft text-[15px] lg:text-[17px]">
          <strong>{t("alertLimit", { n: limit })}</strong>{" "}<span className="text-muted">{t("alertLimitNever")}</span>
        </p>
      )}
      {row("inspection_accuracy", "inspection", 0, 1, 0.05, (v) => `${Math.round(v * 100)}%`)}
      <button onClick={reset} className="btn btn-outline w-full mt-2">{t("reset")}</button>
    </aside>
  );
}
