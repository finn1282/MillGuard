import type { Action, Outlook } from "../lib/types";
import { pct, rm } from "../lib/format";
import { useLang } from "../lib/i18n";

type Money = Pick<Outlook, "risk_pct" | "rm_breakdown_cost" | "rm_at_risk" | "rm_cost_to_act" | "rm_saved_if_acted">;

function Maths({ m, wholeMill }: { m: Money; wholeMill?: boolean }) {
  const { t } = useLang();
  return <div className="font-num text-[13px] lg:text-base mt-0.5 lg:mt-1">
    {t(wholeMill ? "mathsLineMill" : "mathsLine", { pct: pct(m.risk_pct), rm: rm(m.rm_breakdown_cost) })}
  </div>;
}

const Row = ({ label, value, cls = "" }: { label: React.ReactNode; value: string; cls?: string }) => (<>
  <div className="min-w-0">{label}</div>
  <span className={`font-num font-bold text-right text-[21px] lg:text-[30px] ${cls}`}>{value}</span>
</>);

// Dark "You protect" bar when acting saves money.
export function DecisionBar({ action, title }: { action: Action; title: string }) {
  const { t } = useLang();
  const atStop = action.recommendation === "schedule_next_stop";
  return (
    <div className="bg-ink text-paper rounded p-[18px] lg:p-7 flex flex-col gap-3.5 lg:gap-[22px]">
      <p className="m-0 text-[21px] lg:text-[28px] font-extrabold leading-tight">{title}</p>
      <div className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-3 lg:gap-x-5 gap-y-2.5 lg:gap-y-3.5 border-t border-[#3A4046] pt-3.5 lg:pt-5 items-baseline">
        <Row cls="text-db-loss" value={rm(action.rm_at_risk)} label={<>
          <div className="text-[15px] lg:text-lg text-db-label">{t("expectedLoss")}</div>
          <div className="text-db-sub"><Maths m={action} wholeMill={action.criticality === "whole_mill"} /></div>
        </>} />
        <Row value={rm(action.rm_cost_to_act)}
          label={<div className="text-[15px] lg:text-lg text-db-label">{t(atStop ? "fixAtStopMinus" : "fixNowMinus")}</div>} />
        <span className="col-span-2 h-0.5 lg:h-[3px] bg-paper" />
        <div className="text-[17px] lg:text-[22px] font-extrabold">{t("youProtect")}</div>
        <span className="font-num font-extrabold text-right text-db-protect tracking-tight text-[36px] lg:text-[54px] leading-none flex-wrap">
          {rm(action.rm_saved_if_acted)}
        </span>
      </div>
    </div>
  );
}

// Light bar when there is no action, or acting saves nothing (saved = 0).
export function OutlookBar({ m, title, wholeMill }: { m: Money; title: string; wholeMill?: boolean }) {
  const { t } = useLang();
  const cheaperToWait = m.rm_saved_if_acted <= 0;
  return (
    <div className="sec flex flex-col gap-3.5 lg:gap-[18px]">
      <p className="m-0 text-[21px] lg:text-[28px] font-extrabold leading-tight">{title}</p>
      <div className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-3 lg:gap-x-5 gap-y-2.5 lg:gap-y-3.5 border-t border-rule-soft pt-3.5 lg:pt-[18px] items-baseline">
        <Row value={rm(m.rm_at_risk)} label={<>
          <div className="text-[15px] lg:text-lg">{t("expectedLoss")}</div>
          <div className="text-muted"><Maths m={m} wholeMill={wholeMill} /></div>
        </>} />
        <Row value={rm(m.rm_cost_to_act)} label={<div className="text-[15px] lg:text-lg">{t("costToFix")}</div>} />
        <span className="col-span-2 h-0.5 lg:h-[3px] bg-ink" />
        <div className="text-[17px] lg:text-xl font-extrabold">{t(cheaperToWait ? "waitingCheaper" : "actingSaves")}</div>
        <span className="font-num font-extrabold text-right text-ok text-[30px] lg:text-[40px] leading-none">
          {rm(cheaperToWait ? m.rm_cost_to_act - m.rm_at_risk : m.rm_saved_if_acted)}
        </span>
      </div>
    </div>
  );
}
