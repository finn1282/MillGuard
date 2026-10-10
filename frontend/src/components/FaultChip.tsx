import { faultColor } from "../lib/faultColors";

const PATHS: Record<string, string> = {
  worm_wear: "M6 3l12 4.5L6 12l12 4.5L6 21",
  bearing: "M12 3a9 9 0 1 0 0 18 9 9 0 1 0 0-18zM12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 1 0 0-7z",
  gearbox_shaft: "M12 6a6 6 0 1 0 0 12 6 6 0 1 0 0-12zM12 2v4M12 18v4M2 12h4M18 12h4M4.9 4.9l2.8 2.8M16.3 16.3l2.8 2.8M4.9 19.1l2.8-2.8M16.3 7.7l2.8-2.8",
  hydraulic_cone: "M4 5h16l-6 15h-4z",
  electrical: "M13 2L4 14h7l-1 8 9-12h-7z",
  unknown: "M9 9a3 3 0 1 1 4.2 2.7c-.8.4-1.2 1.1-1.2 1.9V15M12 19v.01",
  boiler_steam: "M7 21c-2-3 2-5 0-9s2-6 0-9M12 21c-2-3 2-5 0-9s2-6 0-9M17 21c-2-3 2-5 0-9s2-6 0-9",
  boiler_water: "M12 3s6 7 6 11.5a6 6 0 0 1-12 0C6 10 12 3 12 3z",
};

export function FaultIcon({ fc, size = 18 }: { fc: string; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2}
      strokeLinecap="round" strokeLinejoin="round" className="flex-none" aria-hidden>
      <path d={PATHS[fc] ?? PATHS.unknown} />
    </svg>
  );
}

// Square icon chip in the fault class colour (accent border, tint fill, AA ink icon).
export function FaultBadge({ fc, size = 36 }: { fc: string; size?: number }) {
  const c = faultColor(fc);
  return (
    <span className="flex-none inline-flex items-center justify-center rounded-[6px] border-2"
      style={{ width: size, height: size, background: c.tint, borderColor: c.accent, color: c.ink }}>
      <FaultIcon fc={fc} size={Math.round(size * 0.55)} />
    </span>
  );
}

// Fault name chip: same colours everywhere a fault class appears.
export function FaultChip({ fc, children, className = "" }: { fc: string; children: React.ReactNode; className?: string }) {
  const c = faultColor(fc);
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-[4px] border font-bold leading-tight ${className}`}
      style={{ background: c.tint, borderColor: c.accent, color: c.ink }}>
      <FaultIcon fc={fc} size={16} />{children}
    </span>
  );
}
