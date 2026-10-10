import type { Diagnosis, FingerprintCheck } from "../lib/types";
import { useLang, type Key } from "../lib/i18n";
import { IconCross, IconPending, IconTick, IconWatch } from "./Icons";

const PENDING = /^(Not yet|Belum lagi)\s*:?\s*/i;
const isPending = (c: FingerprintCheck) => !c.matches && PENDING.test(c.observed_en);

// Rows are keyed by (signal, expected): one signal can appear more than once.
export function Fingerprint({ d }: { d: Diagnosis }) {
  const { t, pick } = useLang();
  const rows = d.fingerprint;
  const n = rows.filter((r) => r.matches).length;
  return (
    <div className="sec pb-2 lg:pb-2.5">
      <div className="flex justify-between items-baseline gap-2 lg:gap-3 flex-wrap mb-1.5 lg:mb-2.5">
        <p className="label">{t("fingerprint")} — {pick(d, "name")}</p>
        <span className="text-sm lg:text-base font-bold">{t("nOfM", { n, m: rows.length })}</span>
      </div>
      <div className="hidden lg:grid grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)_150px] gap-4 pb-3.5 text-base text-muted font-semibold">
        <span>{t("usualSign")}</span><span>{t("seenNow")}</span><span>{t("match")}</span>
      </div>
      {rows.map((r) => {
        const pending = isPending(r);
        const raw = pick(r, "observed").replace(PENDING, "");
        const seen = raw.charAt(0).toUpperCase() + raw.slice(1);
        const status = r.matches
          ? <span className="inline-flex items-center gap-1.5 font-bold text-base text-ok"><IconTick size={20} />{t("yes")}</span>
          : pending
            ? <span className="inline-flex items-center gap-1.5 font-bold text-base text-muted"><IconPending size={20} />{t("notYet")}</span>
            : <span className="inline-flex items-center gap-1.5 font-bold text-base text-muted"><IconCross size={20} />{t("no")}</span>;
        const sign = `${pick(r, "label")} ${t(`exp_${r.expected}` as Key)}`;
        return (
          <div key={`${r.signal}:${r.expected}`}
            className="border-t border-rule-soft py-3 lg:py-3.5 grid grid-cols-[minmax(0,1fr)_auto] lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)_150px] gap-x-3 lg:gap-4 items-center">
            <div className="min-w-0">
              <div className={`text-base lg:text-[17px] font-bold ${r.matches ? "" : "text-muted"}`}>{sign}</div>
              <div className="lg:hidden text-sm text-muted">{seen}</div>
            </div>
            <span className="hidden lg:block text-base">{seen}</span>
            {status}
          </div>
        );
      })}
      {n < rows.length / 2 && (
        <div className="flex gap-2.5 items-start bg-[#FFFBEB] border border-sample-border rounded-[4px] px-3 py-2.5 mt-2.5 mb-2 text-[15px] lg:text-base leading-snug text-watch-ink">
          <IconWatch size={18} className="mt-0.5" />{t("early", { n, m: rows.length })}
        </div>
      )}
    </div>
  );
}
