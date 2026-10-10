import { useEffect, useState } from "react";
import { AssumptionsDrawer } from "../components/AssumptionsDrawer";
import { FaultBadge } from "../components/FaultChip";
import { IconAct, IconTick } from "../components/Icons";
import { PageBar } from "../components/PageBar";
import { ErrorBox, Loading } from "../components/States";
import { api } from "../lib/api";
import { faultColor } from "../lib/faultColors";
import { num, rm } from "../lib/format";
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
        <button onClick={() => setDrawer(true)} className="btn btn-outline self-start min-h-[44px] text-[15px] lg:text-base">{t("seeAll")}</button>
        <section aria-labelledby="guide" className="flex flex-col gap-3.5 lg:gap-4">
          <div className="flex justify-between items-baseline gap-3 flex-wrap">
            <h1 id="guide" className="m-0 text-2xl lg:text-[30px] font-extrabold">{t("faultGuide")}</h1>
            <span className="text-[15px] lg:text-[17px] text-muted">{t("faultGuideSub")}</span>
          </div>
          {faults.error ? <ErrorBox error={faults.error} retry={faults.retry} /> : !faults.data ? <Loading /> : (
            <div className="grid gap-3.5 grid-cols-[repeat(auto-fill,minmax(min(100%,330px),1fr))]">
              {faults.data.map((f) => <FaultCard key={f.fault_class} f={f} />)}
            </div>
          )}
        </section>
        <RobustnessSection faults={faults.data ?? []} />
      </div>
      <AssumptionsDrawer open={drawer} onClose={() => setDrawer(false)} />
    </>
  );
}

function FaultCard({ f }: { f: FaultGuide }) {
  const { t, pick, lang } = useLang();
  const steps = lang === "ms" ? f.fix_steps_ms : f.fix_steps_en;
  const c = faultColor(f.fault_class);
  const dt = "mt-3.5 mb-1 text-[13px] lg:text-sm tracking-[.08em] uppercase text-muted font-bold";
  return (
    <article id={`fault-${f.fault_class}`} style={{ borderLeftColor: c.accent }}
      className="bg-card border border-rule border-l-[6px] rounded overflow-hidden flex flex-col scroll-mt-6">
      <div className="flex items-center gap-3 px-5 py-3.5 border-b border-rule-soft" style={{ background: c.tint }}>
        <FaultBadge fc={f.fault_class} />
        <h3 className="m-0 flex-1 min-w-0 text-xl lg:text-[22px] font-extrabold leading-tight" style={{ color: c.ink }}>{pick(f, "name")}</h3>
      </div>
      <div className="px-5 pb-5 pt-3 flex flex-col">
        <div>
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
      </div>
    </article>
  );
}

function RobustnessSection({ faults }: { faults: FaultGuide[] }) {
  const { t, pick } = useLang();
  const res = useApi(api.robustness, []);
  if (res.error) return <ErrorBox error={res.error} retry={res.retry} />;
  if (!res.data) return <Loading />;
  const r: Robustness = res.data;
  const fname = (fc: string) => { const f = faults.find((x) => x.fault_class === fc); return f ? pick(f, "name") : fc; };
  const tm = r.test_mill;
  const sum = tm?.by_fault_class.reduce((s, x) => ({ total: s.total + x.total, caught: s.caught + x.caught }), { total: 0, caught: 0 });
  if (!tm || !sum) return null;

  return (
    <section aria-labelledby="robust" className="flex flex-col gap-3.5 lg:gap-4">
      <h2 id="robust" className="m-0 text-2xl lg:text-[30px] font-extrabold">{t("robustness")}</h2>
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
                <td className="py-2.5 pr-2 font-bold"><span className="inline-flex items-center gap-2.5"><FaultBadge fc={x.fault_class} size={26} />{fname(x.fault_class)}</span></td>
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
    </section>
  );
}
