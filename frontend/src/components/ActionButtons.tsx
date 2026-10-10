import { useState } from "react";
import { api } from "../lib/api";
import type { Action, Recommendation } from "../lib/types";
import { useLang } from "../lib/i18n";
import { IconThumb, IconTick } from "./Icons";

// The recommended action is the only filled button. Saved = 0 makes Keep watching the recommendation.
export function ActionButtons({ action, recorded, onRecorded }: { action: Action; recorded: boolean; onRecorded: () => void }) {
  const { t, pick } = useLang();
  const [chosen, setChosen] = useState<Recommendation>();
  const rec: Recommendation = action.rm_saved_if_acted <= 0 ? "monitor" : action.recommendation;
  const label = pick(action, "deadline_label");
  const text: Record<Recommendation, string> = {
    fix_now: rec === "fix_now" ? t("fixNowBy", { label }) : t("fixNow"),
    schedule_next_stop: rec === "schedule_next_stop" ? t("scheduleFor", { label }) : t("schedule"),
    monitor: t("keepWatching"),
  };
  const order: Recommendation[] = [rec, ...(["fix_now", "schedule_next_stop", "monitor"] as const).filter((r) => r !== rec)];
  const choose = (d: Recommendation) => { setChosen(d); onRecorded(); api.feedback({ action_id: action.id, decision: d }).catch(() => {}); };
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
      {recorded && <Recorded />}
    </div>
  );
}

export function Useful({ actionId, onRecorded }: { actionId: string; onRecorded: () => void }) {
  const { t } = useLang();
  const [v, setV] = useState<boolean>();
  const send = (useful: boolean) => { setV(useful); onRecorded(); api.feedback({ action_id: actionId, useful }).catch(() => {}); };
  return (
    <div className="flex items-center gap-2.5 justify-center text-sm lg:text-base text-muted">
      {t("useful")}
      {[true, false].map((u) => (
        <button key={String(u)} aria-label={t(u ? "usefulYes" : "usefulNo")} aria-pressed={v === u} onClick={() => send(u)}
          className={`min-h-[44px] px-3 rounded border ${v === u ? "bg-ink text-paper border-ink" : "bg-card text-ink border-control-border"}`}>
          <IconThumb size={18} down={!u} />
        </button>
      ))}
    </div>
  );
}

// One confirmation under the decision buttons after any feedback tap (pinned on mobile, so always in view). Live threshold tuning from feedback is roadmap, not built.
function Recorded() {
  const { t } = useLang();
  return (
    <p role="status" className="m-0 flex items-center justify-center gap-1.5 text-center text-sm lg:text-[15px] text-ok font-bold leading-snug">
      <IconTick size={16} />{t("recorded")}
    </p>
  );
}
