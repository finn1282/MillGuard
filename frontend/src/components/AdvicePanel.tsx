import { useEffect, useState } from "react";
import { api, OfflineUnavailable } from "../lib/api";
import { clock } from "../lib/format";
import { useLang } from "../lib/i18n";
import type { AdviceOut } from "../lib/types";
import { IconAct, IconWatch } from "./Icons";

type State = { kind: "idle" } | { kind: "loading" } | { kind: "done"; a: AdviceOut } | { kind: "error" } | { kind: "offline"; msg?: string };

// "Get detailed advice" under the fix plan (MASTER_PLAN.md §14). EN/BM follows the toggle.
export function AdvicePanel({ assetId, at }: { assetId: string; at: string }) {
  const { t, lang } = useLang();
  const [open, setOpen] = useState(false);
  const [st, setSt] = useState<State>({ kind: "idle" });
  const [secs, setSecs] = useState(0);

  useEffect(() => {
    if (!open) return;
    let live = true;
    setSt({ kind: "loading" }); setSecs(0);
    const tick = setInterval(() => setSecs((s) => s + 1), 1000);
    api.advice(assetId, at, lang).then(
      // Unavailable (no key, no network, no fault): sections is [] and message explains why.
      (a) => live && setSt(a.sections?.length ? { kind: "done", a } : { kind: "offline", msg: a.message || a.title }),
      (e) => live && setSt({ kind: e instanceof OfflineUnavailable ? "offline" : "error" }),
    ).finally(() => clearInterval(tick));
    return () => { live = false; clearInterval(tick); };
  }, [open, assetId, at, lang]);

  if (!open) {
    return <button onClick={() => setOpen(true)} className="btn btn-strong w-full">{t("getAdvice")}</button>;
  }

  return (
    <section aria-live="polite" aria-busy={st.kind === "loading"} className="sec flex flex-col gap-3.5">
      {st.kind === "loading" && (
        <div role="status" className="flex flex-col gap-3 py-1">
          <p className="m-0 text-base lg:text-lg font-bold">{t("adviceLoading")}</p>
          <div className="h-1.5 bg-paper rounded-chip overflow-hidden" aria-hidden>
            <div className="h-full w-1/3 bg-ink rounded-chip animate-[advice_1.6s_ease-in-out_infinite]" />
          </div>
          <p className="m-0 text-sm lg:text-base text-muted font-num">{t("adviceWait", { s: secs })}</p>
        </div>
      )}
      {st.kind === "error" && (
        <div role="alert" className="flex flex-wrap items-center gap-3">
          <p className="m-0 flex-1 min-w-[12rem] text-base">{t("adviceError")}</p>
          <button className="btn btn-outline min-h-[44px]" onClick={() => { setOpen(false); setTimeout(() => setOpen(true)); }}>{t("retry")}</button>
        </div>
      )}
      {st.kind === "offline" && <p className="m-0 text-base text-muted">{st.msg || t("adviceOffline")}</p>}
      {st.kind === "done" && <AdviceBody a={st.a} />}
      <button onClick={() => { setOpen(false); setSt({ kind: "idle" }); }}
        className="self-start bg-transparent border-0 p-0 min-h-[44px] text-[15px] font-bold text-[#1D4ED8] hover:underline">{t("hideAdvice")}</button>
    </section>
  );
}

function AdviceBody({ a }: { a: AdviceOut }) {
  const { t, lang } = useLang();
  return (<>
    <p className="m-0 flex gap-2 items-start bg-watch-bg border border-watch-border text-watch-ink rounded-[4px] px-3 py-2.5 text-sm lg:text-base font-bold leading-snug">
      <IconWatch size={18} className="mt-0.5" />{t("adviceLabel")}
    </p>
    <h3 className="m-0 text-xl lg:text-2xl font-extrabold leading-tight">{a.title}</h3>
    {a.sections.map((s, i) => {
      // Safety is flagged by position (3rd in the contract order) as well as by name, so BM headings work too.
      const safety = i === 2 || /^(safety|keselamatan)/i.test(s.heading);
      return (
        <div key={i} className={safety ? "bg-act-tint border border-[#F3C9AE] rounded-[4px] p-3.5" : "border-t border-rule-soft pt-3"}>
          <h4 className="m-0 mb-2 flex items-center gap-2 label text-ink">{safety && <IconAct size={16} className="text-act" />}{s.heading}</h4>
          <ul className="m-0 pl-5 flex flex-col gap-1.5 text-[15px] lg:text-[17px] leading-snug">
            {s.items.map((x, j) => <li key={j}>{x}</li>)}
          </ul>
        </div>
      );
    })}
    {a.sources.length > 0 && (
      <div className="border-t border-rule-soft pt-3">
        <p className="label mb-2">{t("sources")}</p>
        <ul className="m-0 pl-5 flex flex-col gap-1 text-[15px] lg:text-base">
          {a.sources.map((s, i) => <li key={i}>{s.url ? <a href={s.url} target="_blank" rel="noopener noreferrer">{s.label}</a> : s.label}</li>)}
        </ul>
      </div>
    )}
    <p className="m-0 text-sm lg:text-base text-ink-2 leading-snug">{a.disclaimer}</p>
    <p className="m-0 text-[13px] lg:text-sm text-muted font-num">
      {t("generatedBy", { model: a.model })} · {clock(a.generated_at, lang)}{a.cached && ` · ${t("savedCopy")}`}
    </p>
  </>);
}
