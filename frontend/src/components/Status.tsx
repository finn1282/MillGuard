import type { AssetStatus } from "../lib/types";
import { useLang } from "../lib/i18n";
import { IconAct, IconTick, IconWatch } from "./Icons";

const STYLE: Record<AssetStatus, string> = {
  act: "bg-act text-white border border-act",
  watch: "bg-watch-bg text-watch-ink border border-watch-border",
  ok: "bg-ok-bg text-ok-ink border border-ok-border",
};

export function StatusIcon({ status, size = 18 }: { status: AssetStatus; size?: number }) {
  if (status === "act") return <IconAct size={size} />;
  if (status === "watch") return <IconWatch size={size} />;
  return <IconTick size={size} />;
}

// Status is never colour alone: colour + icon + word.
export function StatusChip({ status, small }: { status: AssetStatus; small?: boolean }) {
  const { t } = useLang();
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-chip font-bold leading-tight ${STYLE[status]}
      ${small ? "text-sm px-2.5 py-1" : "text-base px-3 py-1"}`}>
      <StatusIcon status={status} size={small ? 14 : 16} />
      {t(status)}
    </span>
  );
}

export function NotMonitoredChip() {
  const { t } = useLang();
  return (
    <span className="inline-flex items-center rounded-chip border border-dashed border-control-border text-muted font-bold text-sm px-2.5 py-1">
      {t("notMonitored")}
    </span>
  );
}
