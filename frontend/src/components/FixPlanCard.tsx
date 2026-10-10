import { useState } from "react";
import type { FixPlan } from "../lib/types";
import { useLang } from "../lib/i18n";
import { IconAct, IconTick } from "./Icons";

export function FixPlanCard({ fix }: { fix: FixPlan }) {
  const { t, lang, pick } = useLang();
  const steps = lang === "ms" ? fix.steps_ms : fix.steps_en;
  const [done, setDone] = useState<Set<number>>(new Set());
  const toggle = (i: number) => setDone((d) => { const n = new Set(d); n.has(i) ? n.delete(i) : n.add(i); return n; });
  return (
    <div className="sec">
      <div className="flex flex-col lg:flex-row lg:justify-between lg:items-baseline gap-1.5 lg:gap-3 flex-wrap mb-2 lg:mb-3">
        <p className="label">{t("fixPlan")}</p>
        <span className="text-sm lg:text-base font-semibold">
          {t("crewMeta", { crew: fix.crew, h: fix.est_hours })} · {t(`stop_${fix.stop}`)}
        </span>
      </div>
      <ol className="m-0 p-0 list-none">
        {steps.map((s, i) => (
          <li key={i} className="border-t border-rule-soft">
            <label className="flex gap-3 lg:gap-3.5 items-start py-2.5 lg:py-3 text-[15px] lg:text-[17px] leading-snug cursor-pointer">
              <input type="checkbox" checked={done.has(i)} onChange={() => toggle(i)}
                className="w-5 h-5 lg:w-[22px] lg:h-[22px] flex-none mt-0.5 accent-ink" />
              <span className={done.has(i) ? "line-through text-muted" : ""}>{s}</span>
            </label>
          </li>
        ))}
      </ol>
      {fix.parts.length > 0 && (
        <div className="flex flex-wrap gap-1.5 lg:gap-2 mt-2.5 lg:mt-3.5 items-center">
          <span className="text-[13px] lg:text-base text-muted font-bold">{t("parts")}</span>
          {fix.parts.map((p) => (
            <span key={p.name_en} className="text-sm lg:text-base bg-paper rounded-[4px] px-2 lg:px-2.5 py-1.5">{pick(p, "name")} ×{p.qty}</span>
          ))}
        </div>
      )}
      <p className={`mt-2.5 lg:mt-3.5 mb-0 text-sm lg:text-base font-bold flex gap-2 items-start ${fix.lost_production ? "text-loss" : "text-ok"}`}>
        {fix.lost_production ? <IconAct size={18} className="mt-0.5" /> : <IconTick size={18} className="mt-0.5" />}
        {t(fix.lost_production ? "lostProd" : "noLostProd")}
      </p>
    </div>
  );
}
