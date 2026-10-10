import { AnimatePresence, motion } from "framer-motion";
import { useEffect } from "react";
import { api } from "../lib/api";
import { useLang } from "../lib/i18n";
import { useApi } from "../lib/useApi";
import { IconTick, IconWatch } from "./Icons";
import { ErrorBox, Loading } from "./States";

// /api/assumptions is English only, by contract.
export function AssumptionsDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t, lang } = useLang();
  const res = useApi(open ? api.assumptions : null, [open]);
  useEffect(() => {
    if (!open) return;
    const k = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [open, onClose]);
  return (
    <AnimatePresence>
      {open && (<>
        <motion.div key="bg" className="fixed inset-0 z-40 bg-overlay" onClick={onClose}
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} />
        <motion.aside key="panel" role="dialog" aria-modal="true" aria-labelledby="asm-title"
          className="fixed z-50 inset-x-0 bottom-0 top-12 lg:top-0 lg:left-auto lg:w-[640px] bg-paper rounded-t-2xl lg:rounded-none flex flex-col"
          initial={{ y: 40, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 40, opacity: 0 }} transition={{ duration: 0.2 }}>
          <div className="flex items-start gap-3 p-4 lg:p-6 border-b border-rule bg-card lg:rounded-none rounded-t-2xl">
            <div className="flex-1 min-w-0">
              <h2 id="asm-title" className="m-0 text-xl lg:text-2xl font-extrabold">{t("assumptions")}</h2>
              <p className="mt-1.5 mb-0 text-sm lg:text-base text-muted">{t("assumptionsNote")}{lang === "ms" && ` ${t("englishOnly")}`}</p>
            </div>
            <button onClick={onClose} className="btn btn-outline min-h-[44px]" autoFocus>{t("close")}</button>
          </div>
          <div className="flex-1 overflow-y-auto p-4 lg:p-6 pb-24">
            {res.error && <ErrorBox error={res.error} retry={res.retry} />}
            {!res.data && !res.error && <Loading />}
            {res.data && (
              <ul className="m-0 p-0 list-none bg-card border border-rule rounded">
                {res.data.map((a, i) => (
                  <li key={a.key} className={`p-3.5 lg:p-4 flex flex-col gap-1 ${i ? "border-t border-rule-soft" : ""}`}>
                    <div className="flex flex-wrap justify-between items-baseline gap-x-3 gap-y-1">
                      <span className="font-bold text-base lg:text-[17px]">{a.label}</span>
                      <span className="font-num font-bold text-base">{typeof a.value === "number" ? a.value.toLocaleString("en-MY", { maximumFractionDigits: 6 }) : a.value} <span className="text-muted font-normal">{a.unit}</span></span>
                    </div>
                    <div className="flex flex-wrap items-start justify-between gap-x-3 gap-y-1">
                      <span className="text-sm text-muted min-w-0 break-words">{a.source}</span>
                      {a.status === "validated"
                        ? <span className="inline-flex items-center gap-1 text-sm font-bold rounded-chip px-2 py-0.5 bg-ok-bg text-ok-ink border border-ok-border"><IconTick size={14} />{t("validated")}</span>
                        : <span className="inline-flex items-center gap-1 text-sm font-bold rounded-chip px-2 py-0.5 bg-watch-bg text-watch-ink border border-watch-border"><IconWatch size={14} />{t("assumed")}</span>}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </motion.aside>
      </>)}
    </AnimatePresence>
  );
}
