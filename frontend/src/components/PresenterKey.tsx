import { useEffect, useRef, useState } from "react";
import { demoKey, setDemoKey } from "../lib/api";
import { useLang } from "../lib/i18n";
import { IconWatch } from "./Icons";

// Presenter key for write calls: session storage only, never in the URL or the build.
export function KeyField({ onDone, autoFocus }: { onDone?: () => void; autoFocus?: boolean }) {
  const { t } = useLang();
  const [v, setV] = useState(demoKey() ?? "");
  return (
    <form className="sec border-2 border-watch-border flex flex-col gap-3"
      onSubmit={(e) => { e.preventDefault(); if (v.trim()) { setDemoKey(v.trim()); onDone?.(); } }}>
      <p className="m-0 flex items-center gap-2 text-lg font-extrabold text-watch-ink"><IconWatch size={20} />{t("gwLocked")}</p>
      <label htmlFor="gw-key" className="text-base font-bold">{t("gwKey")}</label>
      <div className="flex gap-2.5">
        <input id="gw-key" type="password" autoComplete="off" autoFocus={autoFocus} value={v} onChange={(e) => setV(e.target.value)}
          className="flex-1 min-w-0 min-h-[50px] px-3 rounded border-2 border-control-border bg-card text-lg font-num" />
        <button className="btn btn-primary">{t("gwUnlock")}</button>
      </div>
      <p className="m-0 text-sm text-muted">{t("gwKeyNote")}</p>
    </form>
  );
}

// Modal shell on the native <dialog>: Esc and the close button both close it.
export function Modal({ open, onClose, label, children }: { open: boolean; onClose: () => void; label: string; children: React.ReactNode }) {
  const { t } = useLang();
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);
  return (
    <dialog ref={ref} aria-label={label} onClose={onClose} onClick={(e) => { if (e.target === ref.current) onClose(); }}
      className="w-[min(32rem,calc(100vw-32px))] p-0 rounded bg-paper text-ink backdrop:bg-overlay">
      {open && (
        <div className="flex flex-col gap-3 p-4">
          {children}
          <button onClick={onClose} className="btn btn-outline self-end min-h-[44px]">{t("close")}</button>
        </div>
      )}
    </dialog>
  );
}

// Small inline link after a 401 on a write call; opens the key field in a dialog.
export function KeyNeededLink() {
  const { t } = useLang();
  const [open, setOpen] = useState(false);
  return (
    <>
      <button type="button" onClick={() => setOpen(true)}
        className="self-center inline-flex items-center gap-1.5 text-sm lg:text-[15px] font-bold text-link underline underline-offset-2 min-h-[44px]">
        <IconWatch size={16} />{t("keyNeeded")}
      </button>
      <Modal open={open} onClose={() => setOpen(false)} label={t("gwKey")}>
        <KeyField autoFocus onDone={() => setOpen(false)} />
      </Modal>
    </>
  );
}
