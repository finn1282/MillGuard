import { useEffect, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { ActionButtons } from "../components/ActionButtons";
import { AdvicePanel } from "../components/AdvicePanel";
import { DecisionBar, OutlookBar } from "../components/Decision";
import { FaultBadge, FaultChip } from "../components/FaultChip";
import { Fingerprint } from "../components/Fingerprint";
import { IconAct, IconCross, IconTick } from "../components/Icons";
import { Sparkline } from "../components/Sparkline";
import { StatusIcon } from "../components/Status";
import { ErrorBox, Loading } from "../components/States";
import { api } from "../lib/api";
import { useClock } from "../lib/clock";
import { dayMonth, hhmm, num, pct, rm } from "../lib/format";
import { useLang } from "../lib/i18n";
import type { AssetDetail, AssetStatus, FaultGuide, Series } from "../lib/types";
import { faultColor } from "../lib/faultColors";
import { useApi } from "../lib/useApi";
import { useStickyTop } from "../lib/useStickyTop";

const LAST = "mg.machine";

// /machine without an id: last machine viewed, else the top card tonight, else the first machine.
export function Machine() {
  const { id } = useParams();
  const { at } = useClock();
  const brief = useApi(!id && at ? () => api.brief(at) : null, [id, at]);
  useEffect(() => { if (id) try { sessionStorage.setItem(LAST, id); } catch { /* private mode */ } }, [id]);
  if (id) return <MachineView id={id} />;
  let last: string | null = null;
  try { last = sessionStorage.getItem(LAST); } catch { /* private mode */ }
  if (last) return <Navigate to={`/machine/${last}`} replace />;
  if (brief.error) return <Navigate to="/machine/press_1" replace />;
  if (!brief.data) return <Loading />;
  return <Navigate to={`/machine/${brief.data.actions[0]?.asset_id ?? "press_1"}`} replace />;
}

const BAND: Record<AssetStatus, string> = {
  act: "bg-act text-white",
  watch: "bg-watch-bg text-watch-ink border-b-2 border-watch-border",
  ok: "bg-ok-bg text-ok-ink border-b-2 border-ok",
};

function MachineView({ id }: { id: string }) {
  const { at } = useClock();
  const { t, pick, lang, name, unit } = useLang();
  const res = useApi(at ? () => api.asset(id, at) : null, [id, at]);
  const faults = useApi(api.faults, []);
  const line = useApi(at ? () => api.line(at) : null, [at]);
  const sticky = useStickyTop(24);
  const [recorded, setRecorded] = useState(false);
  useEffect(() => setRecorded(false), [id, at]);

  if (res.error) return <ErrorBox error={res.error} retry={res.retry} />;
  if (!res.data) return <Loading />;
  const d: AssetDetail = res.data;
  const a = d.action;
  const o = d.outlook;
  const fname = (fc: string) => faults.data?.find((f: FaultGuide) => f.fault_class === fc);
  const wholeMill = a?.criticality === "whole_mill" || d.fix?.stop === "whole_mill";
  const saved = a ? a.rm_saved_if_acted > 0 : false;

  const bandRight = a ? `${t("deadline")} · ${pick(a, "deadline_label")}`
    : d.status === "ok" ? t("nothingTonight") : t("notAlertYet");

  const when = a ? (a.recommendation === "schedule_next_stop" ? t("atStop", { label: pick(a, "deadline_label") }) : pick(a, "deadline_label")) : "";
  const riskStrong = (s: string) => {
    const p = pct(a?.risk_pct ?? o?.risk_pct ?? d.risk_pct);
    const [before, after] = s.split(p);
    return <>{before}<strong className="font-num text-lg lg:text-2xl">{p}</strong>{after}</>;
  };
  const riskLine = a
    ? riskStrong(t("ifNotFixed", { when, pct: pct(a.risk_pct), window: pick(a, "window_label") }))
    : o ? <>{d.status === "ok" ? t("allNormal") : pick(d.asset, "summary")} · {riskStrong(t("chanceOnly", { pct: pct(o.risk_pct), window: pick(o, "window_label") }))}</>
      : pick(d.asset, "summary");
  const hero = a?.rm_at_risk ?? o?.rm_at_risk;

  // Evidence: the action's 3 reasons, else the fingerprint signals, else every signal.
  const bySignal = (s: string) => d.series.find((x) => x.signal === s);
  const evidence: { s: Series; title: string; hot: boolean }[] = a
    ? a.reasons.flatMap((r, i) => { const s = bySignal(r.signal); return s ? [{ s, title: `${i + 1} · ${pick(r, "text")}`, hot: i === 0 }] : []; })
    : d.diagnosis
      ? [...new Set(d.diagnosis.fingerprint.map((f) => f.signal))].flatMap((sig) => { const s = bySignal(sig); return s ? [{ s, title: pick(s, "label"), hot: true }] : []; })
      : d.series.map((s) => ({ s, title: pick(s, "label"), hot: false }));

  const peers = line.data?.assets ?? [];
  const guide = d.diagnosis ? fname(d.diagnosis.fault_class) : undefined;

  return (
    <div className={`page ${a ? "pb-[260px] lg:pb-14" : ""}`}>
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
        <Link to="/mill" className="text-[15px] lg:text-[17px] font-semibold">{t("backToMill")}</Link>
        {peers.length > 0 && (
          <nav aria-label={t("machines")} className="flex flex-wrap gap-1.5 lg:ml-auto">
            {peers.map((p) => (
              <Link key={p.id} to={`/machine/${p.id}`} aria-current={p.id === id ? "page" : undefined}
                className={`inline-flex items-center gap-1.5 min-h-[40px] px-2.5 rounded border text-sm font-bold no-underline
                  ${p.id === id ? "bg-brand text-white border-brand" : "bg-card text-ink border-rule"}`}>
                <StatusIcon status={p.status} size={14} />{name(p)}
              </Link>
            ))}
          </nav>
        )}
      </div>

      <header className="bg-card border border-rule rounded overflow-hidden">
        <div className={`flex flex-wrap items-center gap-x-2.5 gap-y-1 px-4 lg:px-6 py-2.5 lg:py-3 font-extrabold text-[15px] lg:text-lg tracking-wider uppercase ${BAND[d.status]}`}>
          <StatusIcon status={d.status} size={20} />{t(d.status)}
          <span className="flex-1" />
          <span className="font-semibold normal-case tracking-normal text-sm lg:text-[17px]">{bandRight}</span>
        </div>
        {wholeMill && a && (
          <div className="flex items-start gap-3 px-4 lg:px-6 py-3 lg:py-3.5 bg-act-tint border-b border-act-tint-border text-base lg:text-lg">
            <IconAct size={20} className="text-act mt-0.5" />
            <span><strong>{t("whyFirst")}</strong> {pick(a, "why_rank")}</span>
          </div>
        )}
        <div className="flex flex-wrap gap-x-10 gap-y-3 lg:gap-y-6 justify-between items-end p-4 lg:px-6 lg:pt-[22px] lg:pb-[26px]">
          <div className="flex flex-col gap-1 lg:gap-1.5 min-w-0 basis-[min(100%,34rem)] grow">
            <div className="text-sm lg:text-[17px] text-muted font-semibold">{t(d.asset.type === "boiler" ? "stationBoiler" : "stationPress")}</div>
            <h1 className="m-0 text-[28px] lg:text-[40px] font-extrabold leading-tight">{name(d.asset)}</h1>
            <p className="mt-1 lg:mt-1.5 mb-0 text-base lg:text-[21px] leading-snug">{riskLine}</p>
          </div>
          {hero != null && (
            <div className="ml-auto text-right">
              <p className="label">{t("expectedLoss")}</p>
              <div className={`rm-hero ${a ? "text-loss" : "text-ink"}`}>{rm(hero)}</div>
            </div>
          )}
        </div>
      </header>

      <div className="grid gap-3.5 lg:gap-6 lg:grid-cols-2 items-start">
        {/* A · problem */}
        <section aria-labelledby="sec-a" className="flex flex-col gap-3.5 lg:gap-4 min-w-0">
          <H2 id="sec-a" letter="A">{t(d.diagnosis ? "whatsWrong" : "whatWeChecked")}</H2>
          {d.diagnosis && (
            <div className="sec border-l-[6px] flex flex-col gap-2.5 lg:gap-3.5" style={{ borderLeftColor: faultColor(d.diagnosis.fault_class).accent }}>
              <p className="label">{t("diagnosis")}</p>
              <div className="flex justify-between items-center gap-2 lg:gap-3 flex-wrap">
                <h3 className="m-0 flex items-center gap-2.5 lg:gap-3 text-[22px] lg:text-[30px] font-extrabold leading-tight">
                  <FaultBadge fc={d.diagnosis.fault_class} size={36} />{pick(d.diagnosis, "name")}
                </h3>
                <span className="text-sm lg:text-[17px] text-muted whitespace-nowrap">
                  <strong className="font-num text-lg lg:text-2xl text-ink">{pct(d.diagnosis.confidence_pct)}</strong> {t("confident")}
                </span>
              </div>
              <p className="m-0 text-base lg:text-[19px] leading-normal text-ink-2">{pick(d.diagnosis, "plain")}</p>
              {d.diagnosis.alternatives.some((x) => x.confidence_pct >= 1) && (
                <div className="flex gap-1.5 lg:gap-2.5 flex-wrap items-center">
                  <span className="text-sm lg:text-base text-muted">{t("lessLikely")}</span>
                  {d.diagnosis.alternatives.filter((x) => x.confidence_pct >= 1).map((x) => (
                    <FaultChip key={x.fault_class} fc={x.fault_class} className="text-sm lg:text-base px-2 lg:px-2.5 py-1.5">
                      {fname(x.fault_class) ? pick(fname(x.fault_class)!, "name") : x.fault_class} <span className="font-num">{pct(x.confidence_pct)}</span>
                    </FaultChip>
                  ))}
                </div>
              )}
            </div>
          )}
          {a && at && <AdvicePanel key={`${id}@${at}`} assetId={id} at={at} />}
          {d.diagnosis && d.diagnosis.fingerprint.length > 0 && <Fingerprint d={d.diagnosis} />}

          {evidence.length > 0 && (
            <div className="sec pb-1.5 lg:pb-2.5">
              <div className="flex flex-wrap justify-between items-baseline gap-x-3 gap-y-1 mb-1">
                <p className="label">{t(a ? "evidence" : "signals7d")}</p>
                {o?.handled_at && (
                  <span className="inline-flex items-center gap-1.5 text-sm lg:text-base font-bold text-ok">
                    <span aria-hidden className="w-0.5 h-4 bg-ok" />{t("repaired", { when: `${dayMonth(o.handled_at, lang)} · ${hhmm(o.handled_at)}` })}
                  </span>
                )}
              </div>
              {evidence.map(({ s, title, hot }, i) => (
                <div key={s.signal + i} className={`grid grid-cols-[minmax(0,1fr)_auto] gap-2.5 lg:gap-5 items-center py-3 lg:py-3.5 ${i ? "border-t border-rule-soft" : ""}`}>
                  <div className="min-w-0">
                    <div className="text-[15px] lg:text-[17px] font-bold">{title}</div>
                    <div className="font-num text-[13px] lg:text-base text-muted mt-0.5">
                      {pick(s, "summary")}{s.limit != null && ` · ${t("limit")} ${num(s.limit, 1)} ${unit(s)}`}
                    </div>
                  </div>
                  <Sparkline points={s.points} limit={s.limit} hot={hot} handledAt={o?.handled_at}
                    label={`${pick(s, "label")}: ${pick(s, "summary")}`} />
                </div>
              ))}
            </div>
          )}

          <div className="sec flex flex-col gap-2.5 lg:gap-3">
            <p className="label">{t("history")}</p>
            {d.history.length === 0 && <p className="m-0 text-[15px] lg:text-[17px] text-muted">{t("noHistory")}</p>}
            {d.history.map((h) => (
              <div key={h.t} className="flex justify-between gap-x-3 gap-y-1 text-[15px] lg:text-[17px] flex-wrap">
                <span><span className="font-num text-muted">{dayMonth(h.t, lang)}</span> · {pick(h, "what")}</span>
                {h.was_predicted
                  ? <span className="inline-flex items-center gap-1.5 font-bold text-sm lg:text-base text-ok"><IconTick size={18} />{t("predicted")}</span>
                  : <span className="inline-flex items-center gap-1.5 font-bold text-sm lg:text-base text-loss"><IconCross size={18} />{t("missed")}</span>}
              </div>
            ))}
            {guide && (
              <Link to={`/how#fault-${guide.fault_class}`} className="text-[15px] lg:text-[17px] font-bold mt-1">
                {t("learnAbout", { name: pick(guide, "name").toLowerCase() })}
              </Link>
            )}
          </div>
        </section>

        {/* B · fix */}
        <section aria-labelledby="sec-b" ref={sticky.ref} style={{ top: sticky.top }}
          className="flex flex-col gap-3.5 lg:gap-4 min-w-0 lg:sticky">
          <H2 id="sec-b" letter="B">{t("whatToDo")}</H2>
          {a && saved && <DecisionBar action={a} title={pick(a, "headline")} />}
          {a && !saved && <OutlookBar m={a} title={t("keepWatching")} wholeMill={wholeMill} />}
          {!a && o && <OutlookBar m={o} wholeMill={d.asset.type === "boiler"}
            title={d.status === "ok" ? t("nothingKeepRunning") : t("keepWatching")} />}
          {!a && o && pick(o, "note") && (
            <p className="m-0 flex gap-2.5 items-start bg-ok-bg border border-ok-border text-ok-ink rounded px-3.5 py-3 text-[15px] lg:text-[17px] leading-snug">
              <IconTick size={18} className="mt-0.5" />{pick(o, "note")}
            </p>
          )}

          {!a && (d.last_service || d.next_check) && (
            <div className="sec grid grid-cols-2 gap-5">
              {d.last_service && <div className="min-w-0">
                <p className="label">{t("lastService")}</p>
                <div className="text-base lg:text-xl font-bold mt-2">{pick(d.last_service, "what")}</div>
                <div className="font-num text-sm lg:text-base text-muted mt-1">
                  {dayMonth(d.last_service.t, lang)} · {t("hoursAgo", { h: num(d.last_service.hours_since) })}
                </div>
              </div>}
              {d.next_check && <div className="min-w-0">
                <p className="label">{pick(d.next_check, "label")}</p>
                <div className="font-num text-base lg:text-xl font-bold mt-2">{dayMonth(d.next_check.t, lang)} · {hhmm(d.next_check.t)}</div>
              </div>}
            </div>
          )}
          {!a && <p className="m-0 text-[15px] lg:text-[17px] text-muted leading-normal">{t("watchNote", { name: name(d.asset) })}</p>}

          {a && (<>
            {/* pinned above the tab bar on mobile, inline on desktop */}
            <div className="fixed lg:static inset-x-0 bottom-[var(--tabbar-h)] z-20 bg-card lg:bg-transparent border-t border-rule lg:border-0 shadow-[0_-6px_16px_var(--shadow)] lg:shadow-none px-4 py-3 lg:p-0">
              <ActionButtons key={`${a.id}@${at}`} action={a} recorded={recorded} onRecorded={() => setRecorded(true)} />
            </div>
          </>)}
        </section>
      </div>
    </div>
  );
}

function H2({ id, letter, children }: { id: string; letter: string; children: React.ReactNode }) {
  return (
    <h2 id={id} className="m-0 mt-1.5 lg:mt-0 text-xl lg:text-[26px] font-extrabold flex items-center gap-2 lg:gap-2.5">
      <span className="font-num text-[13px] lg:text-base bg-brand text-white rounded-[4px] px-[7px] lg:px-2 py-0.5 lg:py-[3px]">{letter}</span>
      {children}
    </h2>
  );
}
