import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useClock } from "../lib/clock";
import { useLang } from "../lib/i18n";
import { useSensorName } from "../lib/live";
import type { SensorAlert } from "../lib/types";
import { useApi } from "../lib/useApi";
import { FaultIcon } from "./FaultChip";
import { IconAct, IconCross, IconWatch } from "./Icons";

type Toast =
  | { id: string; kind: "alert"; asset_id: string; fault_class: string }
  | { id: string; kind: "sensor"; alert: SensorAlert };

// Live mode only: one toast per new machine alert id and per new sensor issue. Dismissed after 12 s.
export function LiveToasts() {
  const { live, at } = useClock();
  const { t, pick, name } = useLang();
  const sensorName = useSensorName();
  const on = !!live && !!at;
  const brief = useApi(on ? () => api.brief(at!) : null, [on ? at : null]);
  const line = useApi(on ? () => api.line(at!) : null, [on ? at : null]);
  const faults = useApi(api.faults, []);
  const telegram = useApi(on ? api.notifyStatus : null, [on, live?.session_id]).data?.enabled;
  const seen = useRef(new Set<string>());
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    if (!on) return;
    const fresh: Toast[] = [];
    for (const a of brief.data?.actions ?? []) {
      if (!seen.current.has(a.id)) { seen.current.add(a.id); fresh.push({ id: a.id, kind: "alert", asset_id: a.asset_id, fault_class: a.fault_class }); }
    }
    for (const s of [...(live?.sensor_issues ?? []), ...(brief.data?.sensor_alerts ?? [])]) {
      const id = `sensor|${s.asset_id}|${s.signal}|${s.kind}|${s.first_t}`;
      if (!seen.current.has(id)) { seen.current.add(id); fresh.push({ id, kind: "sensor", alert: s }); }
    }
    if (!fresh.length) return;
    setToasts((ts) => [...fresh, ...ts].slice(0, 4));
    for (const f of fresh) setTimeout(() => setToasts((ts) => ts.filter((x) => x.id !== f.id)), 12_000);
  }, [on, brief.data, live?.sensor_issues]);

  if (!on || !toasts.length) return null;
  const asset = (id: string) => { const a = line.data?.assets.find((x) => x.id === id); return a ? name(a) : id; };
  const fault = (fc: string) => { const f = faults.data?.find((x) => x.fault_class === fc); return f ? pick(f, "name") : fc; };
  const close = (id: string) => setToasts((ts) => ts.filter((x) => x.id !== id));

  return (
    <div aria-live="polite" className="fixed z-40 inset-x-3 bottom-[calc(var(--tabbar-h)+12px)] lg:inset-x-auto lg:right-6 lg:bottom-6 lg:w-[440px] flex flex-col gap-2.5">
      {/* mobile: newest only, so the page stays readable */}
      {toasts.map((x, i) => (
        <div key={x.id} role="status"
          className={`${i ? "hidden lg:flex" : "flex"} items-start gap-3 rounded border-2 p-3.5 shadow-[0_8px_24px_var(--shadow)] ${x.kind === "alert" ? "bg-card border-act" : "bg-watch-tint border-watch-border"}`}>
          <span className={`flex-none w-9 h-9 rounded-full flex items-center justify-center ${x.kind === "alert" ? "bg-act text-white" : "bg-watch-bg text-watch-ink"}`}>
            {x.kind === "alert" ? <IconAct size={18} /> : <IconWatch size={18} />}
          </span>
          <div className="flex-1 min-w-0 text-base leading-snug">
            {x.kind === "alert" ? (<>
              <p className="m-0 font-extrabold">
                <span className="inline-block align-[-2px] mr-1.5"><FaultIcon fc={x.fault_class} size={16} /></span>{t("toastAlert", { asset: asset(x.asset_id), fault: fault(x.fault_class) })}
              </p>
              {telegram && <p className="m-0 text-muted font-semibold">{t("toastSent")}</p>}
              <Link to={`/machine/${x.asset_id}`} onClick={() => close(x.id)} className="inline-block mt-1 font-bold">{t("openMachine", { asset: asset(x.asset_id) })}</Link>
            </>) : (
              <p className="m-0 font-bold text-watch-ink">{t("toastSensor", { asset: asset(x.alert.asset_id), sensor: sensorName(x.alert.signal) })}</p>
            )}
          </div>
          <button aria-label={t("dismiss")} onClick={() => close(x.id)} className="flex-none w-9 h-9 -m-1 rounded flex items-center justify-center text-muted hover:bg-rule-soft">
            <IconCross size={16} />
          </button>
        </div>
      ))}
    </div>
  );
}
