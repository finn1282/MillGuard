import { useEffect, useState } from "react";
import { AssumptionsDrawer } from "../components/AssumptionsDrawer";
import { IconAct, IconFlask, IconTick, IconWatch } from "../components/Icons";
import { PageBar } from "../components/PageBar";
import { ErrorBox, Loading } from "../components/States";
import { api } from "../lib/api";
import { useClock } from "../lib/clock";
import { clock, num, pct, rm } from "../lib/format";
import { useLang, type Key } from "../lib/i18n";
import type { FaultGuide, Robustness } from "../lib/types";
import { useApi } from "../lib/useApi";

export function How() {
  const { t } = useLang();
  const faults = useApi(api.faults, []);
  const [drawer, setDrawer] = useState(false);

  // Arriving from "Learn about …" on the Machine page.
  useEffect(() => {
    if (!faults.data || !location.hash) return;
    document.getElementById(location.hash.slice(1))?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [faults.data]);

  return (
    <>
      <PageBar title={t("howTitle")} />
      <div className="page gap-7 lg:gap-9">
        <Steps />
        <section aria-labelledby="guide" className="flex flex-col gap-3.5 lg:gap-4">
          <div className="flex justify-between items-baseline gap-3 flex-wrap">
            <h2 id="guide" className="m-0 text-2xl lg:text-[30px] font-extrabold">{t("faultGuide")}</h2>
            <span className="text-[15px] lg:text-[17px] text-muted">{t("faultGuideSub")}</span>
          </div>
          {faults.error ? <ErrorBox error={faults.error} retry={faults.retry} /> : !faults.data ? <Loading /> : (
            <div className="grid gap-3.5 grid-cols-[repeat(auto-fill,minmax(min(100%,330px),1fr))]">
              {faults.data.map((f) => <FaultCard key={f.fault_class} f={f} />)}
            </div>
          )}
        </section>
        <Honesty openDrawer={() => setDrawer(true)} />
        <RobustnessSection faults={faults.data ?? []} openDrawer={() => setDrawer(true)} />
      </div>
      <AssumptionsDrawer open={drawer} onClose={() => setDrawer(false)} />
    </>
  );
}

// The five steps, each with the real values from the act-now bookmark's machine.
function Steps() {
  const { t, pick, lang, name: nm } = useLang();
  const { bookmarks } = useClock();
  const bm = bookmarks.find((b) => b.asset_id);
  const res = useApi(bm ? () => api.asset(bm.asset_id!, bm.t) : null, [bm?.t]);
  const d = res.data;
  const a = d?.action;
  const fp = d?.diagnosis?.fingerprint.find((f) => f.matches);
  const ex: (string | null | undefined)[] = [
    d?.series.slice(0, 4).map((s) => pick(s, "label")).join(", "),
    fp && `${pick(fp, "label")}: ${pick(fp, "observed")}`,
    a && d?.diagnosis && `${pct(a.risk_pct)} ${pick(a, "window_label")} · ${pick(d.diagnosis, "name")}, ${pct(d.diagnosis.confidence_pct)}`,
    a && `${rm(a.rm_at_risk)} − ${rm(a.rm_cost_to_act)} = ${rm(a.rm_saved_if_acted)} ${t("protectedWord")}`,
    a?.reasons.map((r) => pick(r, "text")).join(" · "),
  ];
  const name = d ? nm(d.asset) : bm?.asset_id;
  return (
    <section aria-labelledby="steps" className="flex flex-col gap-3.5 lg:gap-4">
      <div>
        <h1 id="steps" className="m-0 text-[26px] lg:text-4xl font-extrabold">{t("fiveSteps")}</h1>
        {bm && name && <p className="mt-1.5 mb-0 text-base lg:text-lg text-muted">{t("followedWith", { name, when: clock(bm.t, lang) })}</p>}
      </div>
      <ol className="list-none m-0 p-0 grid gap-3 grid-cols-[repeat(auto-fit,minmax(200px,1fr))]">
        {(["s1", "s2", "s3", "s4", "s5"] as const).map((k, i) => (
          <li key={k} className="sec p-5 lg:p-5 flex flex-col gap-2.5">
            <span className="font-num text-base font-bold text-muted">0{i + 1}</span>
            <h2 className="m-0 text-xl lg:text-2xl font-extrabold">{t(k)}</h2>
            <p className="m-0 text-base lg:text-[17px] leading-snug">{t(`${k}b` as Key)}</p>
            {ex[i] && (
              <div className="mt-auto bg-paper rounded-[4px] px-3 py-2.5 text-[15px] lg:text-base leading-snug break-words">
                <strong>{name}:</strong> {ex[i]}
              </div>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}

function FaultCard({ f }: { f: FaultGuide }) {
  const { t, pick, lang } = useLang();
  const steps = lang === "ms" ? f.fix_steps_ms : f.fix_steps_en;
  const dt = "mt-3.5 mb-1 text-[13px] lg:text-sm tracking-[.08em] uppercase text-muted font-bold";
  return (
    <article id={`fault-${f.fault_class}`} className="sec p-5 flex flex-col scroll-mt-6">
      <div className="flex justify-between items-center gap-2 flex-wrap">
        <h3 className="m-0 text-xl lg:text-[22px] font-extrabold">{pick(f, "name")}</h3>
        {f.onset === "gradual"
          ? <span className="inline-flex items-center gap-1.5 text-sm font-bold rounded-chip px-2.5 py-1 bg-ok-bg text-ok-ink border border-ok-border"><IconTick size={14} />{t("gradual")}</span>
          : <span className="inline-flex items-center gap-1.5 text-sm font-bold rounded-chip px-2.5 py-1 bg-watch-bg text-watch-ink border border-watch-border"><IconAct size={14} />{t("sudden")}</span>}
      </div>
      <p className={dt}>{t("whatItIs")}</p><p className="m-0 text-base leading-snug">{pick(f, "what")}</p>
      <p className={dt}>{t("fingerprint")}</p>
      <p className="m-0 text-base leading-snug">{f.signs.map((s) => `${pick(s, "label")} ${t(`exp_${s.expected}` as Key)}`).join(" · ")}</p>
      <p className={dt}>{t("whyItHappens")}</p><p className="m-0 text-base leading-snug">{pick(f, "why")}</p>
      <p className={dt}>{t("standardFix")}</p>
      <ol className="m-0 pl-5 text-base leading-snug flex flex-col gap-1">{steps.map((s, i) => <li key={i}>{s}</li>)}</ol>
      <p className="mt-3.5 mb-0 pt-3 border-t border-rule-soft font-num text-sm text-muted">
        {t("typical", { h: num(f.typical_downtime_h, 1), rm: rm(f.typical_cost_rm) })}
      </p>
    </article>
  );
}

function Honesty({ openDrawer }: { openDrawer: () => void }) {
  const { t } = useLang();
  const { meta } = useClock();
  const asm = useApi(api.assumptions, []);
  const n = (s: "validated" | "assumed") => asm.data?.filter((a) => a.status === s).length;
  const item = (s: string) => <div className="py-2.5 border-t border-rule-soft text-base lg:text-[17px] leading-snug">{s}</div>;
  const cpo = meta ? `RM${meta.mill.cpo_price_rm.toLocaleString("en-MY", { minimumFractionDigits: 2 })}` : "";
  const oer = meta ? `${(meta.mill.oer * 100).toFixed(2)}%` : "";
  return (
    <section aria-labelledby="honesty" className="flex flex-col gap-3.5 lg:gap-4">
      <div>
        <h2 id="honesty" className="m-0 text-2xl lg:text-[30px] font-extrabold">{t("honestyTitle")}</h2>
        <p className="mt-1.5 mb-0 text-base lg:text-lg text-muted">{t("honestySub")}</p>
      </div>
      <div className="grid gap-3.5 grid-cols-[repeat(auto-fit,minmax(min(100%,300px),1fr))]">
        <div className="sec border-t-4 border-t-ok">
          <h3 className="m-0 mb-2 text-xl lg:text-[22px] font-extrabold flex gap-2 items-center"><IconTick size={20} className="text-ok" />{t("real")}</h3>
          {meta && item(t("real1", { cpo, oer }))}{item(t("real2"))}{item(t("real3"))}
          {n("validated") != null && item(t("valCount", { n: n("validated")! }))}
        </div>
        <div className="sec border-t-4 border-t-[#1D4ED8]">
          <h3 className="m-0 mb-2 text-xl lg:text-[22px] font-extrabold flex gap-2 items-center"><IconFlask size={20} className="text-[#1D4ED8]" />{t("simulated")}</h3>
          {item(t("sim1"))}{item(t("sim2"))}{item(t("sim3"))}
        </div>
        <div className="sec border-t-4 border-t-watch-ink">
          <h3 className="m-0 mb-2 text-xl lg:text-[22px] font-extrabold flex gap-2 items-center"><IconWatch size={20} className="text-watch-ink" />{t("assumed")}</h3>
          {n("assumed") != null && item(t("asmCount", { n: n("assumed")! }))}
          {item(t("asmChallenge"))}
          <button onClick={openDrawer} className="mt-2 text-left bg-transparent border-0 p-0 min-h-[44px] text-base lg:text-[17px] font-bold text-[#1D4ED8] hover:underline">{t("seeSources")}</button>
        </div>
      </div>
    </section>
  );
}

function RobustnessSection({ faults, openDrawer }: { faults: FaultGuide[]; openDrawer: () => void }) {
  const { t, pick } = useLang();
  const res = useApi(api.robustness, []);
  if (res.error) return <ErrorBox error={res.error} retry={res.retry} />;
  if (!res.data) return <Loading />;
  const r: Robustness = res.data;
  const fname = (fc: string) => { const f = faults.find((x) => x.fault_class === fc); return f ? pick(f, "name") : fc; };
  const lead = (min: number) => (min >= 120 ? t("hoursShort", { n: num(min / 60) }) : t("minutesShort", { n: num(min) }));
  const tm = r.test_mill;
  const sum = tm?.by_fault_class.reduce((s, x) => ({ total: s.total + x.total, caught: s.caught + x.caught }), { total: 0, caught: 0 });

  return (
    <section aria-labelledby="robust" className="flex flex-col gap-3.5 lg:gap-4">
      <h2 id="robust" className="m-0 text-2xl lg:text-[30px] font-extrabold">{t("robustness")}</h2>

      {tm && sum && (
        <div className="sec">
          <h3 className="m-0 text-lg lg:text-[22px] font-extrabold">{t("testMill", { id: tm.id })}</h3>
          <table className="w-full mt-3 border-collapse text-[15px] lg:text-[17px]">
            <thead>
              <tr className="text-left text-muted text-sm lg:text-base">
                <th className="font-semibold py-2 pr-2">{t("faultType")}</th>
                <th className="font-semibold py-2 px-2 text-right">{t("caught")}</th>
                <th className="font-semibold py-2 pl-2 text-right">{t("medianLead")}</th>
              </tr>
            </thead>
            <tbody>
              {tm.by_fault_class.map((x) => (
                <tr key={x.fault_class} className="border-t border-rule-soft">
                  <td className="py-2.5 pr-2 font-bold">{fname(x.fault_class)}</td>
                  <td className="py-2.5 px-2 text-right font-num whitespace-nowrap">{x.caught} / {x.total}</td>
                  <td className="py-2.5 pl-2 text-right font-num whitespace-nowrap">{x.caught ? t("hoursShort", { n: num(x.median_lead_h) }) : "—"}</td>
                </tr>
              ))}
              <tr className="border-t-2 border-ink">
                <td className="py-2.5 pr-2 font-extrabold">{t("totalRow")}</td>
                <td className="py-2.5 px-2 text-right font-num font-extrabold whitespace-nowrap">{sum.caught} / {sum.total}</td>
                <td />
              </tr>
            </tbody>
          </table>
          <p className="mt-3 mb-0 text-base text-muted">{t("faPerWeek", { n: num(tm.false_alarms_per_week, 1) })}</p>
        </div>
      )}

      <div className="sec flex flex-col gap-2">
        <h3 className="m-0 text-lg lg:text-[22px] font-extrabold">{t("realCompressor", { ds: r.dataset })}</h3>
        <p className="m-0 text-base lg:text-lg">
          <strong className="font-num">{t("caughtXofY", { x: r.caught, y: r.failures_total })}</strong> · {t("faPerWeek", { n: num(r.false_alarms_per_week, 1) })}
        </p>
        <details className="text-[15px] lg:text-base text-ink-2">
          <summary className="cursor-pointer font-bold min-h-[44px] flex items-center">{t("details")}</summary>
          <p className="m-0 leading-normal">{r.note}</p>
        </details>
      </div>

      {r.extra.length > 0 && (
        <div className="flex flex-col gap-3">
          <h3 className="m-0 mt-1 text-lg lg:text-[22px] font-extrabold">{t("otherTests")}</h3>
          <div className="grid gap-3.5 grid-cols-[repeat(auto-fill,minmax(min(100%,360px),1fr))]">
            {r.extra.map((e, i) => (
              <div key={i} className="sec flex flex-col gap-2">
                <p className="label">{e.dataset}</p>
                <p className="m-0 text-base lg:text-lg font-bold leading-snug">{pick(e, "task")}</p>
                <p className="m-0 text-[15px] lg:text-base">
                  <strong className="font-num">{t("caughtXofY", { x: e.events_caught, y: e.events_total })}</strong>
                  {" · "}{t("leadAhead", { t: lead(e.lead_min) })}
                  {" · "}{t("precision", { n: num(e.precision_pct, 1) })}
                  {" · "}{t("faPerDay", { n: num(e.false_alarms_per_day, 2) })}
                </p>
                <details className="text-[15px] lg:text-base text-ink-2">
                  <summary className="cursor-pointer font-bold min-h-[44px] flex items-center">{t("details")}</summary>
                  <p className="m-0 mb-1.5 text-muted">{e.split}</p>
                  <p className="m-0 leading-normal">{e.note}</p>
                </details>
              </div>
            ))}
          </div>
        </div>
      )}
      <button onClick={openDrawer} className="self-start bg-transparent border-0 p-0 min-h-[44px] text-[15px] lg:text-[17px] font-bold text-[#1D4ED8] hover:underline">{t("seeSources")}</button>
    </section>
  );
}
