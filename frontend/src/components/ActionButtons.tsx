import { useState } from "react";
import { api } from "../lib/api";
import { useClock } from "../lib/clock";
import type { Action, Recommendation } from "../lib/types";
import { useLang } from "../lib/i18n";
import { IconPhone, IconTick } from "./Icons";

type Notice = { kind: "sending" } | { kind: "sent"; n: number } | { kind: "off" };

// The recommended action is the only filled button. Saved = 0 makes Keep watching the recommendation.
export function ActionButtons({ action, recorded, onRecorded }: { action: Action; recorded: boolean; onRecorded: () => void }) {
  const { t, pick } = useLang();
  const { at } = useClock();
  const [chosen, setChosen] = useState<Recommendation>();
  const [notice, setNotice] = useState<Notice>();
  const rec: Recommendation = action.rm_saved_if_acted <= 0 ? "monitor" : action.recommendation;
  const label = pick(action, "deadline_label");
  const text: Record<Recommendation, string> = {
    fix_now: rec === "fix_now" ? t("fixNowBy", { label }) : t("fixNow"),
    schedule_next_stop: rec === "schedule_next_stop" ? t("scheduleFor", { label }) : t("schedule"),
    monitor: t("keepWatching"),
  };
  const order: Recommendation[] = [rec, ...(["fix_now", "schedule_next_stop", "monitor"] as const).filter((r) => r !== rec)];
  const choose = (d: Recommendation) => {
    setChosen(d); onRecorded();
    api.feedback({ action_id: action.id, decision: d }).catch(() => {});
    if (d !== "schedule_next_stop" || !at) return setNotice(undefined);
    setNotice({ kind: "sending" });
    api.notifySchedule(at, action.id).then((r) => setNotice(r.ok && r.sent > 0 ? { kind: "sent", n: r.sent } : { kind: "off" }));
  };
  const btn = (r: Recommendation, primary: boolean) => (
    <button key={r} onClick={() => choose(r)} aria-pressed={chosen === r}
      className={`btn inline-flex items-center justify-center gap-2 ${primary ? "btn-primary text-[17px] lg:text-[19px] min-h-[54px] lg:min-h-[60px]"
        : r === "monitor" ? "btn-outline" : "btn-strong"}`}>
      {chosen === r && <IconTick size={18} />}{text[r]}
    </button>
  );
  return (
    <div className="flex flex-col gap-2 lg:gap-2.5">
      {btn(order[0], true)}
      <div className="grid grid-cols-2 gap-2 lg:gap-2.5">{btn(order[1], false)}{btn(order[2], false)}</div>
      {notice ? <Toast n={notice} /> : recorded && <Recorded />}
    </div>
  );
}

// One confirmation after a decision tap. Live threshold tuning from feedback is roadmap, not built.
function Recorded() {
  const { t } = useLang();
  return (
    <p role="status" className="m-0 flex items-center justify-center gap-1.5 text-center text-sm lg:text-[15px] text-ok font-bold leading-snug">
      <IconTick size={16} />{t("recorded")}
    </p>
  );
}

// Schedule: the Telegram result, or that it is not connected.
function Toast({ n }: { n: Notice }) {
  const { t } = useLang();
  const sent = n.kind === "sent";
  return (
    <p role="status" className={`m-0 flex items-center gap-2.5 rounded border px-3 py-2.5 text-sm lg:text-base font-bold leading-snug
      ${sent ? "bg-ok-bg border-ok-border text-ok-ink" : "bg-card border-control-border text-ink"}`}>
      <span className={`flex-none w-8 h-8 rounded-full flex items-center justify-center ${sent ? "bg-ok text-white" : "bg-paper text-muted"}`}>
        <IconPhone size={16} />
      </span>
      {n.kind === "sending" ? t("notifying") : sent ? t("notified", { n: n.n }) : t("notConnected")}
    </p>
  );
}
