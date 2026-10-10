import qrcode from "qrcode-generator";
import { useMemo, useState } from "react";
import { useLang } from "../lib/i18n";
import { Modal } from "./PresenterKey";

// QR of the current page, so judges can open it on their phones. Dark on white in both themes: scanners need it.
function Qr({ text }: { text: string }) {
  const { n, d } = useMemo(() => {
    const q = qrcode(0, "M");
    q.addData(text);
    q.make();
    const n = q.getModuleCount();
    let d = "";
    for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (q.isDark(r, c)) d += `M${c} ${r}h1v1h-1z`;
    return { n, d };
  }, [text]);
  return (
    <svg viewBox={`-3 -3 ${n + 6} ${n + 6}`} role="img" aria-label={text} className="w-full max-w-[280px] mx-auto block rounded" shapeRendering="crispEdges">
      <rect x={-3} y={-3} width={n + 6} height={n + 6} fill="#fff" />
      <path d={d} fill="#000" />
    </svg>
  );
}

export function ShareButton() {
  const { t } = useLang();
  const [open, setOpen] = useState(false);
  const url = open ? location.href : "";
  return (
    <>
      <button onClick={() => setOpen(true)} className="btn btn-outline min-h-[44px] text-sm lg:text-base px-3 flex-none">{t("share")}</button>
      <Modal open={open} onClose={() => setOpen(false)} label={t("shareTitle")}>
        <h2 className="m-0 text-xl font-extrabold">{t("shareTitle")}</h2>
        <Qr text={url} />
        <p className="m-0 text-sm text-muted text-center">{t("shareNote")}</p>
        <p className="m-0 font-num text-base text-center break-all select-all">{url}</p>
      </Modal>
    </>
  );
}
