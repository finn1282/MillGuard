import { useRef, useState } from "react";
import { PageBar } from "../components/PageBar";
import { ErrorBox, Loading } from "../components/States";
import { IconAct, IconWatch } from "../components/Icons";
import { api, clearCache, demoKey, HttpError, setDemoKey, USE_FIXTURES } from "../lib/api";
import { useClock } from "../lib/clock";
import { clock } from "../lib/format";
import { gateway, useGateway } from "../lib/gateway";
import { useLang } from "../lib/i18n";
import { scenarioId, useScenarios } from "../lib/live";
import type { UploadOut } from "../lib/types";

const SPEEDS = [0.5, 1, 2, 4];

// The presenter's console: this page is the sensor gateway (v1.14). Shown on a second screen, so everything is large.
export function Gateway() {
  const { t } = useLang();
  return (
    <>
      <PageBar title={t("gwTitle")} sub={t("gwSub")} />
      <div className="page">
        <p className="m-0 border-l-4 border-info bg-card rounded px-4 py-3 text-base lg:text-lg leading-snug text-ink-2">{t("gwHonest")}</p>
        {USE_FIXTURES ? (
          <div className="sec flex flex-col gap-2">
            <h1 className="m-0 text-2xl lg:text-[30px] font-extrabold">{t("gwOffline")}</h1>
            <p className="m-0 text-base lg:text-lg text-muted">{t("gwOfflineBody")}</p>
          </div>
        ) : <Console />}
      </div>
    </>
  );
}

function Console() {
  const { t, pick, lang } = useLang();
  const { live } = useClock();
  const g = useGateway();
  const list = useScenarios();
  const [busy, setBusy] = useState(false);
  if (list.error && !list.data) return <ErrorBox error={list.error} retry={list.retry} />;
  if (!list.data) return <Loading />;
  const scenarios = list.data;
  const liveId = scenarioId(live?.source);
  const selected = g.scenario ?? liveId ?? scenarios[0]?.id ?? null;
  const sc = scenarios.find((s) => s.id === selected);
  const locked = g.locked;
  const orphan = !!live && !g.running && !!live.live_at && !!liveId;

  const start = async () => {
    if (!sc) return;
    setBusy(true);
    await gateway.start(sc.id, sc.default_start);
    setBusy(false);
  };

  return (
    <div className="grid gap-4 lg:gap-6 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,1fr)] items-start">
      <div className="flex flex-col gap-4 lg:gap-5 min-w-0">
        {locked && <KeyField />}

        <section aria-labelledby="gw-sc" className="sec flex flex-col gap-3">
          <h2 id="gw-sc" className="label">{t("gwScenario")}</h2>
          <div role="radiogroup" aria-labelledby="gw-sc" className="grid gap-2.5 sm:grid-cols-2">
            {scenarios.map((s) => {
              const on = s.id === selected;
              return (
                <button key={s.id} role="radio" aria-checked={on} disabled={g.running || locked} onClick={() => gateway.setScenario(s.id)}
                  className={`text-left rounded p-4 border-2 flex flex-col gap-1.5 ${on ? "border-brand bg-ok-bg" : "border-rule bg-card hover:border-control-border"}`}>
                  <span className="text-lg lg:text-xl font-extrabold leading-tight">{pick(s, "name")}</span>
                  <span className="text-[15px] lg:text-base text-ink-2 leading-snug">{pick(s, "description")}</span>
                </button>
              );
            })}
          </div>
        </section>

        <section aria-labelledby="gw-sp" className="sec flex flex-col gap-3">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 id="gw-sp" className="label">{t("gwSpeed")}</h2>
            <span className="text-sm lg:text-base text-muted">{t("gwSpeedNote")}</span>
          </div>
          <div role="group" aria-labelledby="gw-sp" className="grid grid-cols-4 border-2 border-control-border rounded overflow-hidden">
            {SPEEDS.map((v, i) => (
              <button key={v} aria-pressed={g.speed === v} disabled={locked} onClick={() => gateway.setSpeed(v)}
                className={`min-h-[52px] font-num font-bold text-lg lg:text-xl ${i ? "border-l border-rule" : ""} ${g.speed === v ? "bg-brand text-white" : "bg-card text-ink"}`}>
                {t("gwSpeedOpt", { s: v })}
              </button>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-2.5 mt-1">
            <button onClick={start} disabled={locked || busy || g.running || !sc} className="btn btn-primary min-h-[60px] text-lg lg:text-xl">
              {busy ? t("gwStarting") : t("gwStart")}
            </button>
            <button onClick={() => gateway.stop()} disabled={locked || (!g.running && !live)} className="btn btn-strong min-h-[60px] text-lg lg:text-xl">
              {t("gwStop")}
            </button>
          </div>
          <Status running={g.running} cursor={g.cursor} lang={lang} />
          {orphan && !locked && (
            <div className="flex flex-wrap items-center gap-3 bg-watch-tint border border-watch-border rounded px-3.5 py-3">
              <span className="flex-1 min-w-[14rem] text-base font-bold text-watch-ink">{t("gwNotSending")}</span>
              <button className="btn btn-primary min-h-[44px]" onClick={() => gateway.resume(liveId!, live!.live_at!)}>{t("gwResume")}</button>
            </div>
          )}
          {g.hiddenPause && <p className="m-0 text-base font-bold text-watch-ink">{t("gwPausedHidden")}</p>}
          {g.error && <p role="alert" className="m-0 text-base font-bold text-loss">{g.error}</p>}
          <p className="m-0 text-sm lg:text-base text-muted">{t("gwHidden")}</p>
        </section>

        {scenarios.some((s) => s.upload_enabled) && !locked && <Upload onDone={(id) => { clearCache(); list.retry(); gateway.setScenario(id); }} />}
      </div>

      <Log />
    </div>
  );
}

function Status({ running, cursor, lang }: { running: boolean; cursor: string | null; lang: "en" | "ms" }) {
  const { t } = useLang();
  return (
    <p role="status" className="m-0 flex items-center gap-2.5 text-base lg:text-lg font-bold">
      <span aria-hidden className={`w-3 h-3 rounded-full ${running ? "bg-live animate-pulse" : "bg-control-border"}`} />
      {running && cursor ? t("gwSending", { t: clock(cursor, lang) }) : t("gwIdle")}
    </p>
  );
}

function KeyField() {
  const { t } = useLang();
  const [v, setV] = useState(demoKey() ?? "");
  return (
    <form className="sec border-2 border-watch-border flex flex-col gap-3"
      onSubmit={(e) => { e.preventDefault(); if (v.trim()) { setDemoKey(v.trim()); gateway.unlock(); } }}>
      <p className="m-0 flex items-center gap-2 text-lg font-extrabold text-watch-ink"><IconWatch size={20} />{t("gwLocked")}</p>
      <label htmlFor="gw-key" className="text-base font-bold">{t("gwKey")}</label>
      <div className="flex gap-2.5">
        <input id="gw-key" type="password" autoComplete="off" value={v} onChange={(e) => setV(e.target.value)}
          className="flex-1 min-w-0 min-h-[50px] px-3 rounded border-2 border-control-border bg-card text-lg font-num" />
        <button className="btn btn-primary">{t("gwUnlock")}</button>
      </div>
      <p className="m-0 text-sm text-muted">{t("gwKeyNote")}</p>
    </form>
  );
}

function Log() {
  const { t } = useLang();
  const { live } = useClock();
  const g = useGateway();
  const sent = g.running || !live ? g.sent : Math.max(g.sent, live.readings_ingested);
  return (
    <section aria-labelledby="gw-log" className="bg-ink rounded p-4 lg:p-5 flex flex-col gap-3 min-w-0 lg:sticky lg:top-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="gw-log" className="m-0 text-[13px] lg:text-base tracking-[.08em] uppercase font-bold text-db-label">{t("gwLog")}</h2>
        <span className="font-num font-extrabold text-xl lg:text-2xl text-gold">{t("gwSent", { n: sent.toLocaleString("en-MY") })}</span>
      </div>
      <ol aria-live="off" className="m-0 p-0 list-none flex flex-col gap-1 font-num text-[12px] lg:text-[14px] leading-snug min-h-[200px]">
        {g.log.length === 0 && <li className="text-db-sub">{t("gwLogEmpty")}</li>}
        {g.log.map((l) => (
          <li key={l.id} className={`break-all ${l.issue ? "text-gold font-bold flex gap-1.5" : "text-db-label"}`}>
            {l.issue && <IconAct size={14} className="mt-0.5" />}{l.text}
          </li>
        ))}
      </ol>
    </section>
  );
}

function Upload({ onDone }: { onDone: (scenarioId: string) => void }) {
  const { t } = useLang();
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const [st, setSt] = useState<{ kind: "busy" } | { kind: "done"; r: UploadOut } | { kind: "error"; msg: string }>();
  const send = async (f?: File) => {
    if (!f) return;
    setSt({ kind: "busy" });
    try {
      const r = await api.upload(f);
      setSt({ kind: "done", r }); onDone(r.scenario_id);
    } catch (e) {
      setSt({ kind: "error", msg: e instanceof HttpError && e.status === 401 ? t("gwLocked") : e instanceof Error ? e.message : String(e) });
    }
  };
  return (
    <section aria-labelledby="gw-up" className="sec flex flex-col gap-3">
      <h2 id="gw-up" className="label">{t("upTitle")}</h2>
      <p className="m-0 text-[15px] lg:text-base text-ink-2">{t("upBody")}</p>
      <button type="button" onClick={() => input.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setOver(true); }} onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); send(e.dataTransfer.files[0]); }}
        className={`min-h-[96px] rounded border-2 border-dashed text-base lg:text-lg font-bold ${over ? "border-brand bg-ok-bg" : "border-control-border bg-paper"}`}>
        {st?.kind === "busy" ? t("upBusy") : t("upDrop")}
      </button>
      <input ref={input} type="file" accept=".csv,text/csv" className="hidden" onChange={(e) => send(e.target.files?.[0])} />
      {st?.kind === "done" && (
        <div role="status" className="flex flex-col gap-1.5">
          <p className="m-0 text-base font-bold text-ok">{t("upDone", { rows: st.r.rows.toLocaleString("en-MY"), assets: st.r.assets })}</p>
          {st.r.issues.length === 0 ? <p className="m-0 text-base text-muted">{t("upNoIssues")}</p> : (
            <ul className="m-0 pl-5 text-[15px] text-watch-ink font-bold">{st.r.issues.map((x, i) => <li key={i}>{x}</li>)}</ul>
          )}
        </div>
      )}
      {st?.kind === "error" && <p role="alert" className="m-0 text-base font-bold text-loss">{t("upError", { msg: st.msg })}</p>}
    </section>
  );
}
