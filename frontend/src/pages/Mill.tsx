import { Fragment } from "react";
import { Link } from "react-router-dom";
import { IconTick } from "../components/Icons";
import { NotMonitoredChip, StatusChip } from "../components/Status";
import { ErrorBox, Loading } from "../components/States";
import { api } from "../lib/api";
import { useClock } from "../lib/clock";
import { rm } from "../lib/format";
import { useLang, type Key } from "../lib/i18n";
import type { Action, AssetStatus, LineAsset } from "../lib/types";
import { useApi } from "../lib/useApi";

const BORDER: Record<AssetStatus, string> = { act: "border-2 border-act", watch: "border-2 border-watch-border", ok: "border border-rule" };
const ROW_BG: Record<AssetStatus, string> = { act: "bg-act-tint", watch: "bg-watch-tint", ok: "" };
const BEFORE: Key[] = ["st_ramp", "st_sterilizer", "st_thresher", "st_digesters"];

export function Mill() {
  const { at } = useClock();
  const { t } = useLang();
  const brief = useApi(at ? () => api.brief(at) : null, [at]);
  const line = useApi(at ? () => api.line(at) : null, [at]);

  const err = brief.error ?? line.error;
  if (err) return <ErrorBox error={err} retry={() => { brief.retry(); line.retry(); }} />;
  if (!brief.data || !line.data) return <Loading />;
  const b = brief.data;
  const assets = line.data.assets;
  const watched = assets.filter((a) => a.status === "watch" && !b.actions.some((x) => x.asset_id === a.id));
  const n = b.actions.length;
  const counts = { w: b.watching_count, s: b.suppressed_count };

  return (
    <div className="page">
      {n > 0 ? (
        <header className="sec flex flex-wrap items-end justify-between gap-x-10 gap-y-2.5 lg:gap-y-4">
          <div className="min-w-0">
            <p className="label">{t(b.shift === "night" ? "tonight" : "thisShift")}</p>
            <h1 className="mt-1 lg:mt-1.5 mb-0 text-[26px] lg:text-4xl font-extrabold leading-tight">
              {n === 1 ? t("needYouOne") : t("needYouMany", { n })}
            </h1>
            <p className="mt-2 mb-0 text-sm lg:text-[17px] text-muted">{t(counts.s === 1 ? "alsoCountsOne" : "alsoCounts", counts)}</p>
          </div>
          <div className="ml-auto text-right">
            <p className="label">{t("protectedIfAct")}</p>
            <div className="rm-hero text-ok">{rm(b.rm_protected_total)}</div>
          </div>
        </header>
      ) : (
        <header className="sec border-t-4 border-t-ok flex flex-wrap items-center justify-between gap-x-10 gap-y-3">
          <div className="flex gap-3 lg:gap-[18px] items-center min-w-0">
            <span className="flex-none w-12 h-12 lg:w-14 lg:h-14 rounded-full bg-ok-bg text-ok flex items-center justify-center"><IconTick size={28} /></span>
            <div className="min-w-0">
              <h1 className="m-0 text-[26px] lg:text-4xl font-extrabold leading-tight">
                {t(b.shift === "night" ? "nothingNeedsNight" : "nothingNeedsDay")}
              </h1>
              <p className="mt-2 mb-0 text-[15px] lg:text-lg text-muted">{t(counts.s === 1 ? "countsOne" : "counts", counts)}</p>
            </div>
          </div>
          <div className="ml-auto text-right">
            <p className="label">{t("worthActing")}</p>
            <div className="rm-hero">{rm(b.rm_protected_total)}</div>
          </div>
        </header>
      )}

      <div className="flex flex-wrap gap-3.5 lg:gap-6 items-start">
        <div className="flex flex-col gap-3.5 basis-[380px] grow lg:max-w-[460px] min-w-0">
          {n > 0 && (
            <section aria-labelledby="needs" className="flex flex-col gap-3.5">
              <h2 id="needs" className="m-0 text-[19px] lg:text-2xl font-extrabold">{t("needsYouRanked")}</h2>
              {b.actions.map((a, i) => <ActionCard key={a.id} a={a} rank={i + 1} />)}
            </section>
          )}
          {watched.length > 0 && (
            <section aria-labelledby="watched" className="flex flex-col gap-3.5">
              <h2 id="watched" className="m-0 mt-1 text-[19px] lg:text-2xl font-extrabold">{t("beingWatched")}</h2>
              {watched.map((a) => <WatchCard key={a.id} a={a} />)}
            </section>
          )}
          {n === 0 && b.suppressed_count > 0 && (
            <div className="sec">
              <h3 className="m-0 text-lg lg:text-xl font-extrabold">{b.suppressed_count === 1 ? t("ignoredTitleOne") : t("ignoredTitle", { s: b.suppressed_count })}</h3>
              <p className="mt-2 mb-0 text-[15px] lg:text-[17px] leading-normal text-ink-2">{t("ignoredBody")}</p>
            </div>
          )}
        </div>
        <MillMap assets={assets} />
      </div>
    </div>
  );
}

function ActionCard({ a, rank }: { a: Action; rank: number }) {
  const { t, pick, name } = useLang();
  return (
    <Link to={`/machine/${a.asset_id}`} className={`block bg-card rounded p-4 lg:p-5 text-ink no-underline hover:shadow-md ${BORDER.act}`}>
      <div className="flex justify-between items-center gap-2.5 flex-wrap">
        <span className="text-[21px] lg:text-2xl font-extrabold"><span className="font-num text-muted text-base lg:text-lg">{rank}</span> {name(a)}</span>
        <StatusChip status="act" />
      </div>
      <p className="mt-2.5 lg:mt-3 mb-0 text-base lg:text-lg leading-snug">{pick(a, "headline")}</p>
      {a.criticality === "whole_mill" && (
        <p className="mt-1.5 lg:mt-2 mb-0 text-sm lg:text-base text-loss font-bold">{t("whyFirst")} {pick(a, "why_rank")}</p>
      )}
      <div className="flex flex-wrap justify-between items-end gap-x-2.5 gap-y-1 mt-3 lg:mt-3.5 pt-3 lg:pt-3.5 border-t border-rule-soft">
        <span className="text-[15px] lg:text-[17px]">{pick(a, "deadline_label")}</span>
        {/* saved = 0: same rule as the Machine page, "Waiting is cheaper by" instead of "You protect RM0" */}
        <span className="ml-auto text-right">
          <span className="block text-sm lg:text-base text-muted">
            {a.rm_saved_if_acted > 0 ? t("youProtect").replace(/^=\s*/, "") : t("waitingCheaper")}
          </span>
          <span className={`rm-card ${a.rm_saved_if_acted > 0 ? "text-ok" : "text-ink"}`}>
            {rm(a.rm_saved_if_acted > 0 ? a.rm_saved_if_acted : a.rm_cost_to_act - a.rm_at_risk)}
          </span>
        </span>
      </div>
    </Link>
  );
}

function WatchCard({ a }: { a: LineAsset }) {
  const { at } = useClock();
  const { t, pick, name } = useLang();
  const d = useApi(at ? () => api.asset(a.id, at) : null, [a.id, at]);
  const o = d.data?.outlook;
  return (
    <Link to={`/machine/${a.id}`} className={`block bg-card rounded p-4 lg:p-5 text-ink no-underline hover:shadow-md ${BORDER.watch}`}>
      <div className="flex justify-between items-center gap-2.5 flex-wrap">
        <span className="text-[21px] lg:text-2xl font-extrabold">{name(a)}</span>
        <StatusChip status="watch" />
      </div>
      <p className="mt-2.5 lg:mt-3 mb-0 text-base lg:text-lg leading-snug">{pick(a, "summary")}. {t("watchedNote")}</p>
      {o && (
        <div className="flex justify-between items-baseline flex-wrap gap-2 mt-3 lg:mt-3.5 pt-3 lg:pt-3.5 border-t border-rule-soft">
          <span className="text-[15px] lg:text-[17px]">{t("expectedLoss")}</span>
          <span className="rm-card ml-auto">{rm(o.rm_at_risk)}</span>
        </div>
      )}
    </Link>
  );
}

function Tile({ a }: { a: LineAsset }) {
  const { pick, name } = useLang();
  return (
    <Link to={`/machine/${a.id}`} className={`flex flex-col gap-1.5 p-3 rounded bg-card text-ink no-underline min-w-0 hover:shadow-md ${BORDER[a.status]}`}>
      <div className="flex justify-between items-center gap-2 flex-wrap">
        <span className="text-lg font-extrabold">{name(a)}</span><StatusChip status={a.status} small />
      </div>
      {a.status !== "ok" && <span className="text-base">{pick(a, "summary")}</span>}
    </Link>
  );
}

function Row({ a }: { a: LineAsset }) {
  const { pick, name } = useLang();
  return (
    <Link to={`/machine/${a.id}`} className={`flex justify-between items-center gap-3 px-3.5 py-3 min-h-[52px] border-t border-rule-soft text-ink no-underline ${ROW_BG[a.status]}`}>
      <span className="min-w-0">
        <span className="block text-[17px] font-extrabold">{name(a)}</span>
        {a.status !== "ok" && <span className="text-sm">{pick(a, "summary")}</span>}
      </span>
      <StatusChip status={a.status} small />
    </Link>
  );
}

function MillMap({ assets }: { assets: LineAsset[] }) {
  const { t } = useLang();
  const presses = assets.filter((a) => a.stage === "press").sort((x, y) => x.position - y.position);
  const boilers = assets.filter((a) => a.stage === "boiler");
  const station = (k: Key) => (
    <div key={k} className="flex flex-col gap-1 justify-center p-3 rounded border-2 border-dashed border-[#BDB8AD] bg-[#F8F7F3] text-muted min-w-[104px] flex-1">
      <span className="font-bold text-base">{t(k)}</span><span className="text-sm font-semibold">{t("notMonitored")}</span>
    </div>
  );
  const arrow = <span aria-hidden className="self-center text-muted text-xl">→</span>;
  return (
    <section aria-labelledby="map" className="basis-[560px] grow-[999] min-w-0 flex flex-col gap-3.5">
      {/* desktop: process flow */}
      <div className="hidden lg:flex sec flex-col gap-[18px]">
        <div className="flex justify-between items-baseline gap-3 flex-wrap">
          <h2 id="map" className="m-0 text-2xl font-extrabold">{t("millOrder")}</h2>
          <span className="text-base text-muted">{t("flowsLR")}</span>
        </div>
        <div className="flex gap-2.5 items-stretch flex-wrap">
          {BEFORE.map((k) => <Fragment key={k}>{station(k)}{arrow}</Fragment>)}
          <div className="flex flex-col gap-2 basis-[220px] grow min-w-[220px] p-2.5 rounded bg-paper">
            <div className="text-base font-bold text-muted">{t("stationPress")}</div>
            {presses.map((a) => <Tile key={a.id} a={a} />)}
          </div>
          {arrow}{station("st_clarification")}
        </div>
        <div className="flex gap-4 items-center flex-wrap border-t border-rule-soft pt-[18px]">
          <span className="text-base text-muted font-bold">{t("steamAll")}</span>
          {boilers.map((a) => <div key={a.id} className="basis-[420px] shrink"><Tile a={a} /></div>)}
        </div>
      </div>
      {/* mobile: one list in process order */}
      <div className="lg:hidden flex flex-col gap-3">
        <h2 className="m-0 mt-2 text-[19px] font-extrabold">{t("millOrder")}</h2>
        <div className="bg-card border border-rule rounded overflow-hidden">
          {BEFORE.map((k, i) => (
            <div key={k} className={`flex justify-between items-center gap-3 px-3.5 py-3 ${i ? "border-t border-rule-soft" : ""}`}>
              <span className="font-bold text-muted">{t(k)}</span><NotMonitoredChip />
            </div>
          ))}
          <div className="px-3.5 pt-2.5 pb-1 border-t border-rule-soft label">{t("stationPress")}</div>
          {presses.map((a) => <Row key={a.id} a={a} />)}
          <div className="flex justify-between items-center gap-3 px-3.5 py-3 border-t border-rule-soft">
            <span className="font-bold text-muted">{t("st_clarification")}</span><NotMonitoredChip />
          </div>
          <div className="px-3.5 pt-2.5 pb-1 border-t-2 border-ink label">{t("boilerHouse")}</div>
          {boilers.map((a) => <Row key={a.id} a={a} />)}
        </div>
      </div>
      {assets.length === 0 && <p className="text-muted">{t("noMachines")}</p>}
    </section>
  );
}
