type P = { size?: number; className?: string; label?: string };

function Svg({ size = 20, className, label, sw = 2.6, children }: P & { sw?: number; children: React.ReactNode }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={sw}
      strokeLinecap="round" strokeLinejoin="round" className={`flex-none ${className ?? ""}`}
      role={label ? "img" : undefined} aria-label={label} aria-hidden={label ? undefined : true}>
      {children}
    </svg>
  );
}

export const IconAct = (p: P) => <Svg {...p} sw={2.4}><path d="M12 3l10 18H2z" /><path d="M12 10v5M12 18v.01" /></Svg>;
export const IconWatch = (p: P) => <Svg {...p} sw={2.2}><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></Svg>;
export const IconTick = (p: P) => <Svg {...p} sw={2.8}><path d="M5 12.5l4.5 4.5L19 7.5" /></Svg>;
export const IconCross = (p: P) => <Svg {...p} sw={2.8}><path d="M6 6l12 12M18 6L6 18" /></Svg>;
export const IconPending = (p: P) => <Svg {...p} sw={2.4}><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></Svg>;
export const IconFlask = (p: P) => <Svg {...p} sw={2.2}><path d="M10 3h4M11 3v6L5 19a1 1 0 0 0 .9 1.5h12.2A1 1 0 0 0 19 19l-6-10V3" /></Svg>;
export const IconPhone = (p: P) => <Svg {...p} sw={2.2}><rect x="7" y="2" width="10" height="20" rx="2" /><path d="M11 18h2" /></Svg>;
export const IconPlay = ({ size = 16 }: P) => (
  <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" aria-hidden><path d="M4 2l10 6-10 6z" /></svg>
);
export const IconPause = ({ size = 16 }: P) => (
  <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" aria-hidden><path d="M3 2h4v12H3zM9 2h4v12H9z" /></svg>
);
// MillGuard mark: one arching palm frond, three strokes.
export const PalmMark = (p: P) => <Svg {...p} sw={2.2}><path d="M4 21C7 14 12 8.5 20 5" /><path d="M9.5 13.5C7 13.6 4.8 12.4 3.5 9.8M13.4 9.6c.2-2.5 1.6-4.6 4-6" /><path d="M13 13.6c2.6.6 4.6 2.3 5.5 5" /></Svg>;
export const IconChevron = ({ left, ...p }: P & { left?: boolean }) => (
  <Svg {...p} sw={2.6}><path d={left ? "M15 5l-7 7 7 7" : "M9 5l7 7-7 7"} /></Svg>
);
