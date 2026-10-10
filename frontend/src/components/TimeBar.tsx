import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useClock } from "../lib/clock";
import { clock } from "../lib/format";
import { useLang } from "../lib/i18n";
import { useApi } from "../lib/useApi";
import { IconChevron, IconPause, IconPhone, IconPlay } from "./Icons";
import { SampleBadge } from "./SampleBadge";

export function LangToggle() {
  const { lang, setLang, t } = useLang();
  return (
    <div role="group" aria-label={t("language")} className="flex flex-none border border-control-border rounded overflow-hidden">
      {(["en", "ms"] as const).map((l) => (
        <button key={l} aria-pressed={lang === l} onClick={() => setLang(l)}
          className={`min-h-[44px] px-3 lg:px-3.5 font-bold text-sm lg:text-base ${lang === l ? "bg-brand text-white" : "bg-transparent text-ink"}`}>
          {l === "en" ? "EN" : "BM"}
        </button>
      ))}
    </div>
  );
}

function SendToPhone({ actions }: { actions?: number }) {
  const { at } = useClock();
  const { t } = useLang();
  const status = useApi(api.notifyStatus, []);
  const [msg, setMsg] = useState<string>();
  const [busy, setBusy] = useState(false);
  useEffect(() => setMsg(undefined), [at]);
  if (!status.data?.enabled || !at) return null;
  const send = async () => {
    setBusy(true);
    try {
      // ok false = bot not configured. ok + sent 0 = already sent (one message per alert id), or nothing to send.
      const r = await api.notify(at, "alert");
      setMsg(!r.ok ? t("sendFailed") : r.sent > 0 ? t("sentTo", { n: r.sent }) : actions === 0 ? t("nothingToSend") : t("alreadySent"));
    }
    catch { setMsg(t("sendFailed")); }
    setBusy(false);
  };
  return (
    <span className="hidden lg:inline-flex items-center gap-2">
      <button onClick={send} disabled={busy} className="btn btn-outline min-h-[44px] text-base inline-flex items-center gap-2 px-3">
        <IconPhone size={18} />{busy ? t("sending") : t("sendPhone")}
      </button>
      {msg && <span role="status" className="text-base font-semibold text-muted">{msg}</span>}
    </span>
  );
}

export function TimeBar() {
  const { at, playing, setPlaying, step, bookmarks, setAt } = useClock();
  const { t, lang, pick } = useLang();
  const brief = useApi(at ? () => api.brief(at) : null, [at]);
  const shift = brief.data ? t(brief.data.shift) : "";

  const chips = bookmarks.map((b) => (
    <button key={b.t} aria-pressed={b.t === at} onClick={() => setAt(b.t)}
      className={`flex-none lg:flex-initial max-w-[15rem] lg:max-w-[22rem] text-left leading-tight rounded border font-bold
        text-sm lg:text-base min-h-[40px] lg:min-h-[44px] px-2.5 lg:px-3.5 py-1.5
        ${b.t === at ? "bg-brand border-brand text-white" : "bg-transparent border-control-border text-ink"}`}>
      {pick(b, "label")}
    </button>
  ));

  const controls = (
    <div className="flex items-center gap-1.5 flex-none">
      <button aria-label={t(playing ? "pause" : "play")} onClick={() => setPlaying(!playing)}
        className="w-11 h-11 lg:w-12 lg:h-12 rounded bg-brand text-white flex items-center justify-center">
        {playing ? <IconPause size={14} /> : <IconPlay size={14} />}
      </button>
      <button aria-label={t("back1h")} onClick={() => step(-1)} className="hidden md:flex w-9 h-11 rounded text-ink items-center justify-center hover:bg-rule-soft"><IconChevron left size={18} /></button>
      <button aria-label={t("fwd1h")} onClick={() => step(1)} className="hidden md:flex w-9 h-11 rounded text-ink items-center justify-center hover:bg-rule-soft"><IconChevron size={18} /></button>
    </div>
  );

  const when = (
    <div className="flex flex-col min-w-0">
      <span className="font-num font-bold text-[15px] lg:text-xl whitespace-nowrap">{at ? clock(at, lang) : "—"}</span>
      <span className="text-[13px] lg:text-base text-muted">{shift}<span className="hidden lg:inline">{shift && " · "}{t("replayClock")}</span></span>
    </div>
  );

  return (
    <div className="bg-paper-bar border-b border-rule">
      {/* desktop: real bookmark labels are long, so they get their own row */}
      <div className="hidden lg:flex flex-wrap items-center gap-x-3.5 gap-y-3 px-10 py-3.5">
        <div className="order-1">{controls}</div>
        <div className="order-2">{when}</div>
        <div role="group" aria-label={t("bookmarks")}
          className="order-last basis-full flex flex-wrap gap-2">{chips}</div>
        <div className="order-5 ml-auto flex items-center gap-3.5">
          <SendToPhone actions={brief.data?.actions.length} /><SampleBadge /><LangToggle />
        </div>
      </div>
      {/* mobile + tablet */}
      <div className="lg:hidden flex flex-col gap-2.5 px-4 py-3">
        <div className="flex items-center gap-2.5">
          {controls}
          <div className="flex-1 min-w-0">{when}</div>
          <LangToggle />
        </div>
        <div role="group" aria-label={t("bookmarks")} className="flex gap-2 overflow-x-auto items-center -mx-4 px-4 pb-0.5">
          <SampleBadge />{chips}
        </div>
      </div>
    </div>
  );
}
